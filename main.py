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
        self.max_distance = 50  # Max distance in cm. Objects further than this won't show.
        self.blips = []         

        self.build_ui()
        
        # Give the UI 100ms to physically render on screen before starting the animation loop
        self.after(100, self.update_radar_ui)  

    def build_ui(self):
        # ==========================================
        # LEFT SIDEBAR
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

        self.canvas_width = 600
        self.canvas_height = 300
        self.canvas = tk.Canvas(self.main_panel, width=self.canvas_width, height=self.canvas_height, bg="black", highlightthickness=2, highlightbackground="#333333")
        self.canvas.grid(row=1, column=0, sticky="nsew")

        # FIX: Bind directly to the canvas instead of the panel
        self.canvas.bind("<Configure>", self.on_resize)

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports] if ports else ["No Ports Found"]

    def open_github(self):
        webbrowser.open("https://github.com/bukanluq")

    def on_resize(self, event):
        # FIX: Safety check. Only resize if the window has actually rendered to a normal size
        if event.width > 50 and event.height > 50:
            self.canvas_width = event.width
            self.canvas_height = event.height
            self.draw_radar_background()

    def draw_radar_background(self):
        self.canvas.delete("grid")
        cx = self.canvas_width / 2
        cy = self.canvas_height - 10
        radius = min(self.canvas_width / 2, self.canvas_height) - 20

        # Safety check to prevent negative radius crashes
        if radius <= 0: return

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
        self.canvas.delete("dynamic")

        cx = self.canvas_width / 2
        cy = self.canvas_height - 10
        radius = min(self.canvas_width / 2, self.canvas_height) - 20

        if radius > 0:
            # Draw Sweep Arm
            rad = math.radians(self.current_angle)
            arm_x = cx + (radius * math.cos(rad))
            arm_y = cy - (radius * math.sin(rad))
            self.canvas.create_line(cx, cy, arm_x, arm_y, fill="#4CAF50", width=3, tags="dynamic")

            # Draw Blips
            alive_blips = []
            for blip in self.blips:
                x, y, life = blip
                if life > 0:
                    color_hex = f"#{int(life):02x}0000"
                    self.canvas.create_oval(x-5, y-5, x+5, y+5, fill=color_hex, outline="", tags="dynamic")
                    blip[2] -= 4 # Fade speed
                    alive_blips.append(blip)

            self.blips = alive_blips
            
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

    def serial_loop(self, port, baud):
        try:
            self.serial_conn = serial.Serial(port, int(baud), timeout=0.1) 
            self.after(0, lambda: self.status_dot.configure(text_color="#4CAF50"))
            self.after(0, lambda: self.status_label.configure(text=f"Active on {port}"))
        except Exception as e:
            self.after(0, lambda: self.status_dot.configure(text_color="#FF5252"))
            self.after(0, lambda: self.status_label.configure(text="Port Error"))
            self.after(0, self.stop_listening)
            return

        while self.is_running:
            try:
                if self.serial_conn.in_waiting > 0:
                    raw_data = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    if "," in raw_data:
                        parts = raw_data.split(",")
                        
                        if len(parts) == 2 and parts[0].lstrip('-').isdigit() and parts[1].lstrip('-').isdigit():
                            angle = int(parts[0])
                            distance = int(parts[1])
                            
                            self.current_angle = angle
                            
                            self.after(0, lambda a=angle, d=distance: self.data_label.configure(
                                text=f"Angle: {a:03d}° | Distance: {d:03d} cm"
                            ))

                            if 0 < distance <= self.max_distance:
                                cx = self.canvas_width / 2
                                cy = self.canvas_height - 10
                                radius = min(self.canvas_width / 2, self.canvas_height) - 20
                                
                                if radius > 0:
                                    rad = math.radians(angle)
                                    scaled_dist = (distance / self.max_distance) * radius
                                    
                                    target_x = cx + (scaled_dist * math.cos(rad))
                                    target_y = cy - (scaled_dist * math.sin(rad))
                                    
                                    self.blips.append([target_x, target_y, 255])

            except Exception as e:
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
