import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
import sys
import time
import math
import webbrowser
import tkinter as tk

# --- UI Configuration ---
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class Serial2RadarApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Serial2Radar | Object Visualizer")
        self.geometry("900x600")
        self.minsize(850, 550)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Variables
        self.is_running = False
        self.serial_conn = None
        self.thread = None
        
        # Radar Data
        self.current_angle = 90
        self.max_distance = 50  # Max distance in cm to display on radar
        self.blips = []         # Stores [x, y, life] for detected objects

        self.build_ui()
        self.update_radar_ui()  # Start the animation loop

    def build_ui(self):
        # ==========================================
        # LEFT SIDEBAR: Connection & Settings
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        self.brand_label = ctk.CTkLabel(self.sidebar, text="Serial2Radar", font=("Segoe UI", 24, "bold"))
        self.brand_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.port_var = ctk.StringVar(value="Select Port")
        self.port_dropdown = ctk.CTkOptionMenu(self.sidebar, variable=self.port_var, values=self.get_ports(), width=180)
        self.port_dropdown.grid(row=1, column=0, padx=20, pady=10)

        self.baud_var = ctk.StringVar(value="115200")
        self.baud_dropdown = ctk.CTkOptionMenu(self.sidebar, variable=self.baud_var, values=["9600", "57600", "115200"], width=180)
        self.baud_dropdown.grid(row=2, column=0, padx=20, pady=10)

        self.toggle_btn = ctk.CTkButton(self.sidebar, text="START RADAR", font=("Segoe UI", 13, "bold"),
                                        command=self.toggle_listening, fg_color="#2E7D32", hover_color="#1B5E20", height=40)
        self.toggle_btn.grid(row=3, column=0, padx=20, pady=20)

        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=4, column=0, padx=20, pady=5)
        
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color="gray", font=("Segoe UI", 18))
        self.status_dot.pack(side="left", padx=(0, 5))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Disconnected", font=("Segoe UI", 13))
        self.status_label.pack(side="left")

        # GitHub Button
        self.github_btn = ctk.CTkButton(self.sidebar, text="GitHub @bukanluq", 
                                        command=self.open_github, fg_color="#333333", hover_color="#555555")
        self.github_btn.grid(row=7, column=0, padx=20, pady=20, sticky="s")

        # ==========================================
        # RIGHT MAIN PANEL: Radar Canvas
        # ==========================================
        self.main_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_panel.grid_rowconfigure(1, weight=1)
        self.main_panel.grid_columnconfigure(0, weight=1)

        self.data_label = ctk.CTkLabel(self.main_panel, text="Angle: -- | Distance: -- cm", font=("Consolas", 18, "bold"), text_color="#4CAF50")
        self.data_label.grid(row=0, column=0, pady=(0, 10))

        # Using standard tkinter Canvas for high-performance drawing
        self.canvas_width = 600
        self.canvas_height = 300
        self.canvas = tk.Canvas(self.main_panel, width=self.canvas_width, height=self.canvas_height, bg="black", highlightthickness=2, highlightbackground="#333333")
        self.canvas.grid(row=1, column=0, sticky="nsew")

        # Handle window resizing
        self.main_panel.bind("<Configure>", self.on_resize)

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports] if ports else ["No Ports Found"]

    def open_github(self):
        webbrowser.open("https://github.com/bukanluq")

    def on_resize(self, event):
        # Update canvas dimensions when window resizes
        self.canvas_width = self.canvas.winfo_width()
        self.canvas_height = self.canvas.winfo_height()
        self.draw_radar_background()

    def draw_radar_background(self):
        self.canvas.delete("grid")
        cx = self.canvas_width / 2
        cy = self.canvas_height - 10
        radius = min(self.canvas_width / 2, self.canvas_height) - 20

        # Draw semi-circles
        for i in range(1, 4):
            r = radius * (i / 3)
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=0, extent=180, style=tk.ARC, outline="#1B5E20", tags="grid")

        # Draw angle lines
        for angle in range(0, 181, 30):
            rad = math.radians(angle)
            x = cx + (radius * math.cos(rad))
            y = cy - (radius * math.sin(rad))
            self.canvas.create_line(cx, cy, x, y, fill="#1B5E20", tags="grid")

    def update_radar_ui(self):
        # This function loops to redraw dynamic elements (sweep arm and blips)
        self.canvas.delete("dynamic")

        cx = self.canvas_width / 2
        cy = self.canvas_height - 10
        radius = min(self.canvas_width / 2, self.canvas_height) - 20

        # Draw Sweep Arm
        rad = math.radians(self.current_angle)
        arm_x = cx + (radius * math.cos(rad))
        arm_y = cy - (radius * math.sin(rad))
        self.canvas.create_line(cx, cy, arm_x, arm_y, fill="#4CAF50", width=3, tags="dynamic")

        # Draw Blips (and fade them)
        alive_blips = []
        for blip in self.blips:
            x, y, life = blip
            if life > 0:
                # Convert life (0-255) to a hex color from red to dark red
                color_hex = f"#{int(life):02x}0000"
                
                # Draw the blip
                self.canvas.create_oval(x-4, y-4, x+4, y+4, fill=color_hex, outline="", tags="dynamic")
                
                # Decrease life to simulate fading
                blip[2] -= 5 
                alive_blips.append(blip)

        self.blips = alive_blips # Keep only blips that haven't faded entirely

        # Call this function again after 30ms (~30 FPS)
        self.after(30, self.update_radar_ui)

    def toggle_listening(self):
        if not self.is_running:
            port = self.port_var.get()
            baud = self.baud_var.get()
            
            if port in ("Select Port", "No Ports Found"):
                self.status_dot.configure(text_color="#FF5252")
                self.status_label.configure(text="Invalid Port")
                return

            self.is_running = True
            self.toggle_btn.configure(text="STOP RADAR", fg_color="#C62828", hover_color="#B71C1C")
            self.port_dropdown.configure(state="disabled")
            self.baud_dropdown.configure(state="disabled")
            
            self.thread = threading.Thread(target=self.serial_loop, args=(port, baud), daemon=True)
            self.thread.start()
        else:
            self.stop_listening()

    def stop_listening(self):
        self.is_running = False
        self.toggle_btn.configure(text="START RADAR", fg_color="#2E7D32", hover_color="#1B5E20")
        self.port_dropdown.configure(state="normal")
        self.baud_dropdown.configure(state="normal")
        
        self.status_dot.configure(text_color="gray")
        self.status_label.configure(text="Disconnected")
        self.port_dropdown.configure(values=self.get_ports())

    def serial_loop(self, port, baud):
        try:
            self.serial_conn = serial.Serial(port, int(baud), timeout=0.1) 
            self.status_dot.configure(text_color="#4CAF50")
            self.status_label.configure(text=f"Active on {port}")
        except Exception as e:
            self.status_dot.configure(text_color="#FF5252")
            self.status_label.configure(text="Port Error / In Use")
            self.stop_listening()
            return

        while self.is_running:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode('utf-8').strip()
                    
                    # Expecting format: "Angle,Distance" (e.g., "90,15")
                    if "," in data:
                        parts = data.split(",")
                        if len(parts) == 2:
                            angle = int(parts[0])
                            distance = int(parts[1])
                            
                            self.current_angle = angle
                            
                            # Update Text UI safely from thread
                            self.data_label.configure(text=f"Angle: {angle:03d}° | Distance: {distance:03d} cm")

                            # Add a blip if object is detected within range
                            if 0 < distance <= self.max_distance:
                                cx = self.canvas_width / 2
                                cy = self.canvas_height - 10
                                radius = min(self.canvas_width / 2, self.canvas_height) - 20
                                
                                # Math to calculate pixel position
                                rad = math.radians(angle)
                                scaled_dist = (distance / self.max_distance) * radius
                                
                                target_x = cx + (scaled_dist * math.cos(rad))
                                target_y = cy - (scaled_dist * math.sin(rad))
                                
                                # Add to blips list [x, y, life]
                                self.blips.append([target_x, target_y, 255])

            except Exception:
                pass
            
            time.sleep(0.01)

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def on_closing(self):
        self.stop_listening()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = Serial2RadarApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()