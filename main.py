import customtkinter as ctk
import tkinter as tk
import serial
import serial.tools.list_ports
import threading
import sys
import time
import math
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button as MouseButton

# --- Special Keys & Actions for Keyboard Mapper ---
SPECIAL_KEYS = {
    "Space": Key.space, "Ctrl": Key.ctrl_l, "Shift": Key.shift,
    "Enter": Key.enter, "Esc": Key.esc, "Alt": Key.alt_l, "Tab": Key.tab,
    "Up Arrow": Key.up, "Down Arrow": Key.down, "Left Arrow": Key.left, "Right Arrow": Key.right
}

MOUSE_ACTIONS = [
    "Mouse L-Click", "Mouse R-Click", "Mouse M-Click", 
    "Mouse Up", "Mouse Down", "Mouse Left", "Mouse Right"
]

STANDARD_KEYS = [chr(i) for i in range(97, 123)] + [str(i) for i in range(10)]
ALL_ACTIONS = list(SPECIAL_KEYS.keys()) + MOUSE_ACTIONS + STANDARD_KEYS
SERIAL_CHARS = [chr(i) for i in range(65, 91)] # A-Z

# --- Global UI Configuration ---
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("green")  

def get_available_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports] if ports else ["No Ports Found"]


class KeyboardMapperFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.is_running = False
        self.serial_conn = None
        self.last_data = 'I'
        self.thread = None
        self.mouse_speed = 8 
        
        self.key_map = {
            'W': 'w', 'S': 's', 'A': 'a', 'D': 'd',
            'Z': 'Space', 'E': 'e', 'Q': 'q'
        }
        
        self.keyboard = KeyboardController()
        self.mouse = MouseController()

        self.build_ui()

    def build_ui(self):
        # --- Top Connection Bar ---
        self.conn_frame = ctk.CTkFrame(self, height=60, corner_radius=10)
        self.conn_frame.pack(fill="x", pady=(0, 20), ipadx=10, ipady=10)
        
        self.port_var = ctk.StringVar(value="Select Port")
        self.port_dropdown = ctk.CTkOptionMenu(self.conn_frame, variable=self.port_var, values=get_available_ports(), width=150)
        self.port_dropdown.pack(side="left", padx=10)

        self.baud_var = ctk.StringVar(value="115200")
        self.baud_dropdown = ctk.CTkOptionMenu(self.conn_frame, variable=self.baud_var, values=["9600", "57600", "115200"], width=100)
        self.baud_dropdown.pack(side="left", padx=10)

        self.toggle_btn = ctk.CTkButton(self.conn_frame, text="▶ START LISTENING", font=("Segoe UI", 12, "bold"),
                                        command=self.toggle_listening)
        self.toggle_btn.pack(side="left", padx=20)

        self.status_dot = ctk.CTkLabel(self.conn_frame, text="●", text_color="gray", font=("Segoe UI", 18))
        self.status_dot.pack(side="left", padx=(20, 5))
        
        self.status_label = ctk.CTkLabel(self.conn_frame, text="Disconnected", font=("Segoe UI", 13))
        self.status_label.pack(side="left")

        # --- Main Content Area ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Left Side: Add Mapping
        self.add_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.add_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(self.add_frame, text="Create New Binding", font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
        
        ctk.CTkLabel(self.add_frame, text="Serial Input (A-Z):").pack(pady=(10, 0))
        self.add_serial_var = ctk.StringVar(value="W")
        ctk.CTkOptionMenu(self.add_frame, variable=self.add_serial_var, values=SERIAL_CHARS).pack(pady=(5, 15))

        ctk.CTkLabel(self.add_frame, text="Triggers Action:").pack(pady=(10, 0))
        self.add_action_var = ctk.StringVar(value="Mouse Up")
        ctk.CTkOptionMenu(self.add_frame, variable=self.add_action_var, values=ALL_ACTIONS).pack(pady=(5, 20))

        ctk.CTkButton(self.add_frame, text="+ Add Binding", command=self.add_mapping).pack(pady=10)
        self.error_label = ctk.CTkLabel(self.add_frame, text="", text_color="#FF5252", font=("Segoe UI", 12, "bold"))
        self.error_label.pack(pady=10)

        # Right Side: List of Mappings
        self.list_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.list_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(self.list_frame, text="Active Bindings", font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self.list_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_mapping_list()

    def add_mapping(self):
        serial_char = self.add_serial_var.get()
        action = self.add_action_var.get()

        if serial_char in self.key_map:
            self.error_label.configure(text=f"⚠️ '{serial_char}' is already mapped!")
            return

        self.error_label.configure(text="")
        self.key_map[serial_char] = action
        self.refresh_mapping_list()

    def delete_mapping(self, serial_char):
        if serial_char in self.key_map:
            del self.key_map[serial_char]
            self.error_label.configure(text="") 
            self.refresh_mapping_list()

    def refresh_mapping_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for s_char, action in self.key_map.items():
            row_frame = ctk.CTkFrame(self.scroll_frame, corner_radius=8, fg_color=("gray85", "gray16"))
            row_frame.pack(fill="x", pady=5, padx=5)
            
            s_label = ctk.CTkLabel(row_frame, text=s_char, font=("Segoe UI", 16, "bold"), text_color="#2ECC71", width=30)
            s_label.pack(side="left", padx=(15, 5), pady=10)
            
            ctk.CTkLabel(row_frame, text="➔", font=("Segoe UI", 12), text_color="gray").pack(side="left", padx=5)
            
            a_label = ctk.CTkLabel(row_frame, text=action, font=("Segoe UI", 14, "bold"))
            a_label.pack(side="left", padx=10)

            del_btn = ctk.CTkButton(row_frame, text="✕", width=30, height=28, 
                                    fg_color="transparent", text_color="#FF5252", hover_color="#421010",
                                    command=lambda c=s_char: self.delete_mapping(c))
            del_btn.pack(side="right", padx=10)

    # --- Action Execution Logic ---
    def press_action(self, action):
        if action in SPECIAL_KEYS: self.keyboard.press(SPECIAL_KEYS[action])
        elif action == "Mouse L-Click": self.mouse.press(MouseButton.left)
        elif action == "Mouse R-Click": self.mouse.press(MouseButton.right)
        elif action == "Mouse M-Click": self.mouse.press(MouseButton.middle)
        elif action not in MOUSE_ACTIONS: self.keyboard.press(action)

    def release_action(self, action):
        if action in SPECIAL_KEYS: self.keyboard.release(SPECIAL_KEYS[action])
        elif action == "Mouse L-Click": self.mouse.release(MouseButton.left)
        elif action == "Mouse R-Click": self.mouse.release(MouseButton.right)
        elif action == "Mouse M-Click": self.mouse.release(MouseButton.middle)
        elif action not in MOUSE_ACTIONS: self.keyboard.release(action)

    def handle_continuous_mouse(self, action):
        if action == "Mouse Up": self.mouse.move(0, -self.mouse_speed)
        elif action == "Mouse Down": self.mouse.move(0, self.mouse_speed)
        elif action == "Mouse Left": self.mouse.move(-self.mouse_speed, 0)
        elif action == "Mouse Right": self.mouse.move(self.mouse_speed, 0)

    # --- Core Serial Loop ---
    def toggle_listening(self):
        if not self.is_running:
            port = self.port_var.get()
            baud = self.baud_var.get()
            if port in ("Select Port", "No Ports Found"):
                self.status_dot.configure(text_color="#FF5252")
                self.status_label.configure(text="Invalid Port")
                return

            self.is_running = True
            self.toggle_btn.configure(text="■ STOP LISTENING", fg_color="#C62828", hover_color="#B71C1C")
            self.port_dropdown.configure(state="disabled")
            self.baud_dropdown.configure(state="disabled")
            
            self.thread = threading.Thread(target=self.serial_loop, args=(port, baud), daemon=True)
            self.thread.start()
        else:
            self.stop_listening()

    def stop_listening(self):
        self.is_running = False
        self.toggle_btn.configure(text="▶ START LISTENING", fg_color=['#2CC985', '#2FA572'], hover_color=['#0C955A', '#106A43'])
        self.port_dropdown.configure(state="normal", values=get_available_ports())
        self.baud_dropdown.configure(state="normal")
        self.status_dot.configure(text_color="gray")
        self.status_label.configure(text="Disconnected")

        if self.last_data in self.key_map:
            self.release_action(self.key_map[self.last_data])
        self.last_data = 'I'

    def serial_loop(self, port, baud):
        try:
            self.serial_conn = serial.Serial(port, int(baud), timeout=0.1) 
            self.status_dot.configure(text_color="#2ECC71")
            self.status_label.configure(text=f"Active on {port}")
        except Exception:
            self.status_dot.configure(text_color="#FF5252")
            self.status_label.configure(text="Port Error")
            self.stop_listening()
            return

        while self.is_running:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode('utf-8').strip()
                    if data:
                        if self.last_data in self.key_map:
                            self.release_action(self.key_map[self.last_data])
                        if data in self.key_map:
                            self.press_action(self.key_map[data])
                        self.last_data = data

                if self.last_data in self.key_map:
                    self.handle_continuous_mouse(self.key_map[self.last_data])
                time.sleep(0.01)
            except Exception:
                break

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()


class RadarVisualizerFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.is_running = False
        self.serial_conn = None
        self.thread = None
        
        # Radar Tracking Data
        self.current_angle = 90
        self.sweep_direction = 1 # 1 for right, -1 for left
        self.max_distance = 100  # Default to 100cm
        self.blips = []         

        self.build_ui()
        self.after(100, self.update_radar_ui)  

    def build_ui(self):
        # --- Top Connection Bar ---
        self.conn_frame = ctk.CTkFrame(self, height=60, corner_radius=10)
        self.conn_frame.pack(fill="x", pady=(0, 20), ipadx=10, ipady=10)
        
        self.port_var = ctk.StringVar(value="Select Port")
        self.port_dropdown = ctk.CTkOptionMenu(self.conn_frame, variable=self.port_var, values=get_available_ports(), width=130)
        self.port_dropdown.pack(side="left", padx=10)

        self.baud_var = ctk.StringVar(value="115200")
        self.baud_dropdown = ctk.CTkOptionMenu(self.conn_frame, variable=self.baud_var, values=["9600", "57600", "115200"], width=90)
        self.baud_dropdown.pack(side="left", padx=5)

        self.toggle_btn = ctk.CTkButton(self.conn_frame, text="▶ START RADAR", font=("Segoe UI", 12, "bold"),
                                        command=self.toggle_listening, width=120)
        self.toggle_btn.pack(side="left", padx=15)

        self.status_dot = ctk.CTkLabel(self.conn_frame, text="●", text_color="gray", font=("Segoe UI", 18))
        self.status_dot.pack(side="left", padx=(5, 5))
        
        self.status_label = ctk.CTkLabel(self.conn_frame, text="Offline", font=("Segoe UI", 13), width=60, anchor="w")
        self.status_label.pack(side="left")

        # Range Slider
        ctk.CTkLabel(self.conn_frame, text="Max Range:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(15, 5))
        
        self.range_var = ctk.IntVar(value=100)
        self.range_slider = ctk.CTkSlider(self.conn_frame, variable=self.range_var, from_=20, to=200, width=120, command=self.update_range)
        self.range_slider.pack(side="left", padx=5)
        
        self.range_val_label = ctk.CTkLabel(self.conn_frame, text="100 cm", font=("Segoe UI", 12), width=50, anchor="w")
        self.range_val_label.pack(side="left")

        self.data_label = ctk.CTkLabel(self.conn_frame, text="Angle: -- | Dist: -- cm", font=("Consolas", 16, "bold"), text_color="#2ECC71")
        self.data_label.pack(side="right", padx=20)

        # --- Main Canvas Area ---
        self.canvas_frame = ctk.CTkFrame(self, corner_radius=10)
        self.canvas_frame.pack(fill="both", expand=True)

        self.canvas_width = 800
        self.canvas_height = 400
        self.canvas = tk.Canvas(self.canvas_frame, bg="#0A0F0D", highlightthickness=0) # Darker, radar-like background
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.bind("<Configure>", self.on_resize)

    def update_range(self, val):
        self.max_distance = int(val)
        self.range_val_label.configure(text=f"{self.max_distance} cm")
        self.draw_radar_background() # Redraw the grid to update the text labels

    def on_resize(self, event):
        if event.width > 50 and event.height > 50:
            self.canvas_width = event.width
            self.canvas_height = event.height
            self.draw_radar_background()

    def draw_radar_background(self):
        self.canvas.delete("grid")
        cx = self.canvas_width / 2
        cy = self.canvas_height - 10
        radius = min(self.canvas_width / 2, self.canvas_height) - 20

        if radius <= 0: return

        # Draw distance rings
        for i in range(1, 4):
            r = radius * (i / 3)
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=0, extent=180, style=tk.ARC, outline="#1E5128", dash=(4, 4), tags="grid")
            
            # Distance labels along the vertical axis
            dist_val = int(self.max_distance * (i / 3))
            self.canvas.create_text(cx + 8, cy - r, text=f"{dist_val}cm", fill="#4CAF50", font=("Consolas", 10, "bold"), anchor="w", tags="grid")

        # Draw angle lines
        for angle in range(0, 181, 30):
            rad = math.radians(angle)
            x = cx + (radius * math.cos(rad))
            y = cy - (radius * math.sin(rad))
            self.canvas.create_line(cx, cy, x, y, fill="#1E5128", tags="grid")

    def update_radar_ui(self):
        self.canvas.delete("dynamic")
        cx = self.canvas_width / 2
        cy = self.canvas_height - 10
        radius = min(self.canvas_width / 2, self.canvas_height) - 20

        if radius > 0:
            # 1. Draw Fading Sweep Trail
            trail_colors = ["#2ECC71", "#229954", "#196F3D", "#114A29", "#0A2F1A"]
            for i in range(5):
                trail_ang = self.current_angle - (i * 3 * self.sweep_direction)
                if 0 <= trail_ang <= 180:
                    rad = math.radians(trail_ang)
                    arm_x = cx + (radius * math.cos(rad))
                    arm_y = cy - (radius * math.sin(rad))
                    self.canvas.create_line(cx, cy, arm_x, arm_y, fill=trail_colors[i], width=3 - (i*0.5), tags="dynamic")

            # 2. Draw Main Sweep Arm
            main_rad = math.radians(self.current_angle)
            arm_x = cx + (radius * math.cos(main_rad))
            arm_y = cy - (radius * math.sin(main_rad))
            self.canvas.create_line(cx, cy, arm_x, arm_y, fill="#00FF66", width=3, tags="dynamic")

            # 3. Process and Draw Blips (Shrinking effect for persistence)
            alive_blips = []
            for blip in self.blips:
                if blip["size"] > 0:
                    x, y, size, color = blip["x"], blip["y"], blip["size"], blip["color"]
                    
                    # Draw glowing aura
                    self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline="", tags="dynamic")
                    
                    # Core bright dot
                    if size > 4: 
                        self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="white", outline="", tags="dynamic")
                    
                    blip["size"] -= 0.4 # Fade speed (Shrink over time)
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
            self.toggle_btn.configure(text="■ STOP RADAR", fg_color="#C62828", hover_color="#B71C1C")
            self.port_dropdown.configure(state="disabled")
            self.baud_dropdown.configure(state="disabled")
            self.range_slider.configure(state="disabled") # Lock range during sweep
            
            self.thread = threading.Thread(target=self.serial_loop, args=(port, baud), daemon=True)
            self.thread.start()
        else:
            self.stop_listening()

    def stop_listening(self):
        self.is_running = False
        self.toggle_btn.configure(text="▶ START RADAR", fg_color=['#2CC985', '#2FA572'], hover_color=['#0C955A', '#106A43'])
        self.port_dropdown.configure(state="normal", values=get_available_ports())
        self.baud_dropdown.configure(state="normal")
        self.range_slider.configure(state="normal")
        self.status_dot.configure(text_color="gray")
        self.status_label.configure(text="Offline")

    def serial_loop(self, port, baud):
        try:
            self.serial_conn = serial.Serial(port, int(baud), timeout=0.1) 
            self.after(0, lambda: self.status_dot.configure(text_color="#2ECC71"))
            self.after(0, lambda: self.status_label.configure(text="Active"))
        except Exception:
            self.after(0, lambda: self.status_dot.configure(text_color="#FF5252"))
            self.after(0, lambda: self.status_label.configure(text="Error"))
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
                            
                            # Track Sweep Direction for the visual trail
                            if angle != self.current_angle:
                                self.sweep_direction = 1 if angle > self.current_angle else -1
                            self.current_angle = angle
                            
                            self.after(0, lambda a=angle, d=distance: self.data_label.configure(
                                text=f"Angle: {a:03d}° | Dist: {d:03d} cm"
                            ))

                            # Add Blip if an object is detected within selected max range
                            if 0 < distance <= self.max_distance:
                                cx = self.canvas_width / 2
                                cy = self.canvas_height - 10
                                radius = min(self.canvas_width / 2, self.canvas_height) - 20
                                
                                if radius > 0:
                                    rad = math.radians(angle)
                                    scaled_dist = (distance / self.max_distance) * radius
                                    target_x = cx + (scaled_dist * math.cos(rad))
                                    target_y = cy - (scaled_dist * math.sin(rad))
                                    
                                    # Threat Level Coloring
                                    dist_pct = distance / self.max_distance
                                    if dist_pct < 0.33:
                                        threat_color = "#FF3333" # Red (Close)
                                    elif dist_pct < 0.66:
                                        threat_color = "#FFD700" # Yellow (Mid)
                                    else:
                                        threat_color = "#00E5FF" # Cyan (Far)
                                    
                                    # Append new blip dictionary
                                    self.blips.append({
                                        "x": target_x, 
                                        "y": target_y, 
                                        "size": 8.0, 
                                        "color": threat_color
                                    })
            except Exception:
                pass
            time.sleep(0.01)

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()


class SerialTranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Serial Translator | E21 Academy")
        self.geometry("900x650")
        self.minsize(850, 600)

        # Header Area
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Serial Translator", font=("Segoe UI", 28, "bold"))
        self.title_label.pack(side="left")

        self.brand_label = ctk.CTkLabel(self.header_frame, text="by E21 Academy", font=("Segoe UI", 14), text_color="gray")
        self.brand_label.pack(side="left", padx=(10, 0), pady=(10, 0))

        # View Selector (Segmented Button acting as Tabs)
        self.current_view_name = ctk.StringVar(value="⌨️ Keyboard Mapper")
        self.view_selector = ctk.CTkSegmentedButton(
            self, 
            values=["⌨️ Keyboard Mapper", "📡 Radar Visualizer"],
            variable=self.current_view_name,
            command=self.switch_view,
            font=("Segoe UI", 14, "bold")
        )
        self.view_selector.pack(fill="x", padx=20, pady=10)

        # Container for the active frame
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        # Initialize the frames
        self.frames = {
            "⌨️ Keyboard Mapper": KeyboardMapperFrame(self.main_container),
            "📡 Radar Visualizer": RadarVisualizerFrame(self.main_container)
        }
        
        # Pack the default frame
        self.active_frame = self.frames["⌨️ Keyboard Mapper"]
        self.active_frame.pack(fill="both", expand=True)

    def switch_view(self, view_name):
        # Stop any active serial connections before switching views
        if self.active_frame.is_running:
            self.active_frame.stop_listening()

        # Hide current frame and show the new one
        self.active_frame.pack_forget()
        self.active_frame = self.frames[view_name]
        self.active_frame.pack(fill="both", expand=True)

    def on_closing(self):
        # Gracefully shut down all threads
        for frame in self.frames.values():
            if frame.is_running:
                frame.stop_listening()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = SerialTranslatorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
