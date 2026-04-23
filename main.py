import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import serial
import serial.tools.list_ports
import threading
import sys
import time
import math
import json
from datetime import datetime
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button as MouseButton

# --- Action Mappings ---
SPECIAL_KEYS = {
    "Space": Key.space, "Ctrl": Key.ctrl_l, "Shift": Key.shift,
    "Enter": Key.enter, "Esc": Key.esc, "Alt": Key.alt_l, "Tab": Key.tab,
    "Up Arrow": Key.up, "Down Arrow": Key.down, "Left Arrow": Key.left, "Right Arrow": Key.right
}
MOUSE_BTN_MAP = {
    "Mouse L-Click": MouseButton.left, 
    "Mouse R-Click": MouseButton.right, 
    "Mouse M-Click": MouseButton.middle
}
MOUSE_MOVE_ACTIONS = ["Mouse Up", "Mouse Down", "Mouse Left", "Mouse Right"]

ALL_ACTIONS = list(SPECIAL_KEYS.keys()) + list(MOUSE_BTN_MAP.keys()) + MOUSE_MOVE_ACTIONS + [chr(i) for i in range(97, 123)] + [str(i) for i in range(10)]
SERIAL_CHARS = [chr(i) for i in range(65, 91)] + [str(i) for i in range(10)] 

# --- Global UI Configuration ---
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("green")  

def get_available_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports] if ports else ["No Ports Found"]


class BaseSerialTool(ctk.CTkFrame):
    """
    Centralized Base Class. 
    Handles all threading, connection UI, and serial reading.
    Subclasses only need to implement `handle_serial_data(self, data)` and `build_custom_ui(self)`.
    """
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.is_running = False
        self.serial_conn = None
        self.thread = None
        
        # Build shared Top Bar
        self.build_connection_bar()
        
        # Container for subclass UI
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Build shared Bottom HUD
        self.build_console_hud()
        
        # Let subclass build its specific UI
        self.build_custom_ui()

    def build_connection_bar(self):
        self.conn_frame = ctk.CTkFrame(self, height=60, corner_radius=8)
        self.conn_frame.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)
        
        self.port_var = ctk.StringVar(value="Select Port")
        self.port_dropdown = ctk.CTkOptionMenu(self.conn_frame, variable=self.port_var, values=get_available_ports(), width=140)
        self.port_dropdown.pack(side="left", padx=10)

        self.baud_var = ctk.StringVar(value="115200")
        self.baud_dropdown = ctk.CTkOptionMenu(self.conn_frame, variable=self.baud_var, values=["9600", "57600", "115200"], width=90)
        self.baud_dropdown.pack(side="left", padx=10)

        self.toggle_btn = ctk.CTkButton(self.conn_frame, text="▶ START SYSTEM", font=("Segoe UI", 12, "bold"), width=140, command=self.toggle_listening)
        self.toggle_btn.pack(side="left", padx=20)

        self.status_dot = ctk.CTkLabel(self.conn_frame, text="●", text_color="gray", font=("Segoe UI", 18))
        self.status_dot.pack(side="left", padx=(10, 5))
        self.status_label = ctk.CTkLabel(self.conn_frame, text="Offline", font=("Segoe UI", 13), width=60, anchor="w")
        self.status_label.pack(side="left")

    def build_console_hud(self):
        self.hud_frame = ctk.CTkFrame(self, height=120, corner_radius=8)
        self.hud_frame.pack(fill="x", side="bottom")
        self.hud_frame.pack_propagate(False)
        
        # Subclasses can inject widgets into this frame
        self.active_display_frame = ctk.CTkFrame(self.hud_frame, fg_color="transparent", width=250)
        self.active_display_frame.pack(side="left", fill="y", padx=20, pady=10)
        self.active_display_frame.pack_propagate(False)
        
        self.log_textbox = ctk.CTkTextbox(self.hud_frame, font=("Consolas", 11), fg_color="#121212", text_color="#4CAF50")
        self.log_textbox.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.log_textbox.configure(state="disabled")
        self.add_log("System Ready. Waiting for connection...")

    def build_custom_ui(self):
        """Override this in subclasses to build the middle interface."""
        pass

    def handle_serial_data(self, data):
        """Override this in subclasses to process incoming string data."""
        pass
    
    def system_tick(self):
        """Override this for continuous actions (runs 100x a second)."""
        pass

    def on_stop(self):
        """Override this to clean up specific states when system stops."""
        pass

    def add_log(self, message, is_warning=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.configure(state="normal")
        if is_warning:
            self.log_textbox.insert("end", f"[{timestamp}] [!] {message}\n", "warning")
            self.log_textbox.tag_config("warning", foreground="#FF5252")
        else:
            self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def update_connection_status(self, color, status, log_msg=None, is_warning=False):
        self.status_dot.configure(text_color=color)
        self.status_label.configure(text=status)
        if log_msg:
            self.add_log(log_msg, is_warning)

    def toggle_listening(self):
        if not self.is_running:
            port, baud = self.port_var.get(), self.baud_var.get()
            if port in ("Select Port", "No Ports Found"):
                self.update_connection_status("#FF5252", "Invalid Port")
                return

            self.is_running = True
            self.toggle_btn.configure(text="■ STOP SYSTEM", fg_color="#C62828", hover_color="#B71C1C")
            self.port_dropdown.configure(state="disabled")
            self.baud_dropdown.configure(state="disabled")
            self.add_log(f"Attempting connection to {port}...")
            
            self.thread = threading.Thread(target=self._serial_loop, args=(port, baud), daemon=True)
            self.thread.start()
        else:
            self.stop_listening()

    def stop_listening(self):
        self.is_running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

        self.toggle_btn.configure(text="▶ START SYSTEM", fg_color=['#2CC985', '#2FA572'], hover_color=['#0C955A', '#106A43'])
        self.port_dropdown.configure(state="normal", values=get_available_ports())
        self.baud_dropdown.configure(state="normal")
        self.update_connection_status("gray", "Offline", "System stopped.")
        self.on_stop()

    def _serial_loop(self, port, baud):
        """Centralized loop. Handles errors, reads strings, and passes to subclass."""
        try:
            self.serial_conn = serial.Serial(port, int(baud), timeout=0.1) 
            self.after(0, self.update_connection_status, "#2ECC71", "Active", f"Connected to {port} @ {baud}")
        except Exception as e:
            self.after(0, self.update_connection_status, "#FF5252", "Error", f"Could not open {port}: {e}", True)
            self.after(0, self.stop_listening)
            return

        while self.is_running:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        self.handle_serial_data(data)
                
                self.system_tick()
                time.sleep(0.01)
            except Exception as e:
                self.after(0, self.add_log, f"Connection lost: {e}", True)
                self.after(0, self.stop_listening)
                break


class KeyboardMapperFrame(BaseSerialTool):
    def __init__(self, master):
        self.last_data = 'I'
        self.mouse_speed = 8 
        self.key_map = {'W': 'w', 'S': 's', 'A': 'a', 'D': 'd', 'Z': 'Space'}
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        super().__init__(master)

    def build_custom_ui(self):
        # 1. Main Layout Configuration
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # LEFT PANEL: Configuration
        self.config_frame = ctk.CTkFrame(self.content_frame, corner_radius=8)
        self.config_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # New Binding Section
        ctk.CTkLabel(self.config_frame, text="Create New Binding", font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))
        
        form_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        form_frame.pack(pady=5)
        ctk.CTkLabel(form_frame, text="Serial Input:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.add_serial_var = ctk.StringVar(value="W")
        ctk.CTkOptionMenu(form_frame, variable=self.add_serial_var, values=SERIAL_CHARS, width=100).grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(form_frame, text="Emulates Key:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.add_action_var = ctk.StringVar(value="Mouse Up")
        ctk.CTkOptionMenu(form_frame, variable=self.add_action_var, values=ALL_ACTIONS, width=140).grid(row=1, column=1, padx=10, pady=5)
        
        ctk.CTkButton(self.config_frame, text="+ Add Binding", command=self.add_mapping, width=200).pack(pady=(10, 5))
        self.error_label = ctk.CTkLabel(self.config_frame, text="", text_color="#FF5252", font=("Segoe UI", 12, "bold"))
        self.error_label.pack()

        # Profile Storage
        prof_frame = ctk.CTkFrame(self.config_frame, fg_color=("gray85", "gray16"), corner_radius=8)
        prof_frame.pack(fill="x", padx=20, pady=15, ipady=10)
        ctk.CTkLabel(prof_frame, text="Profile Storage", font=("Segoe UI", 14, "bold")).pack(pady=(5, 5))
        
        btn_frame = ctk.CTkFrame(prof_frame, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text="💾 Save", width=90, fg_color="#333333", command=self.save_profile).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📂 Load", width=90, fg_color="#333333", command=self.load_profile).pack(side="left", padx=5)

        # RIGHT PANEL: Active Bindings List
        self.list_frame = ctk.CTkFrame(self.content_frame, corner_radius=8)
        self.list_frame.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(self.list_frame, text="Active Bindings", font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self.list_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_mapping_list()

        # Update HUD Bottom Left
        ctk.CTkLabel(self.active_display_frame, text="LIVE INPUT HUD", font=("Consolas", 12, "bold"), text_color="gray").pack(anchor="w")
        self.live_input_label = ctk.CTkLabel(self.active_display_frame, text="WAITING...", font=("Consolas", 24, "bold"), text_color="#2ECC71")
        self.live_input_label.pack(anchor="w", pady=(15, 0))

    # --- Tool Specific Logic ---
    def handle_serial_data(self, data):
        """Called by BaseSerialTool thread when a string is received."""
        if self.last_data in self.key_map:
            self.release_action(self.key_map[self.last_data])
        
        if data in self.key_map:
            mapped_action = self.key_map[data]
            self.press_action(mapped_action)
            if data != self.last_data:
                self.after(0, self.update_hud, data, mapped_action)
        else:
            if data != self.last_data:
                self.after(0, self.reset_hud)
                
        self.last_data = data

    def system_tick(self):
        """Called continuously by BaseSerialTool thread."""
        if self.last_data in self.key_map:
            action = self.key_map[self.last_data]
            if action == "Mouse Up": self.mouse.move(0, -self.mouse_speed)
            elif action == "Mouse Down": self.mouse.move(0, self.mouse_speed)
            elif action == "Mouse Left": self.mouse.move(-self.mouse_speed, 0)
            elif action == "Mouse Right": self.mouse.move(self.mouse_speed, 0)

    def on_stop(self):
        """Release keys when connection stops."""
        if self.last_data in self.key_map: 
            self.release_action(self.key_map[self.last_data])
        self.last_data = 'I'
        self.reset_hud()

    def update_hud(self, s_char, action):
        self.add_log(f"Triggered: [{s_char}] ➔ {action}")
        self.live_input_label.configure(text=f"[{s_char}] ➔ {action}", text_color="#2ECC71")

    def reset_hud(self):
        self.live_input_label.configure(text="WAITING...", text_color="gray")

    def press_action(self, action):
        if action in SPECIAL_KEYS: self.keyboard.press(SPECIAL_KEYS[action])
        elif action in MOUSE_BTN_MAP: self.mouse.press(MOUSE_BTN_MAP[action])
        elif action not in MOUSE_MOVE_ACTIONS: self.keyboard.press(action)

    def release_action(self, action):
        if action in SPECIAL_KEYS: self.keyboard.release(SPECIAL_KEYS[action])
        elif action in MOUSE_BTN_MAP: self.mouse.release(MOUSE_BTN_MAP[action])
        elif action not in MOUSE_MOVE_ACTIONS: self.keyboard.release(action)

    def add_mapping(self):
        serial_char = self.add_serial_var.get()
        if serial_char in self.key_map:
            self.error_label.configure(text=f"⚠️ '{serial_char}' is already mapped!")
            return
        self.error_label.configure(text="")
        self.key_map[serial_char] = self.add_action_var.get()
        self.refresh_mapping_list()

    def delete_mapping(self, serial_char):
        if serial_char in self.key_map:
            del self.key_map[serial_char]
            self.refresh_mapping_list()

    def refresh_mapping_list(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        for s_char, action in self.key_map.items():
            row = ctk.CTkFrame(self.scroll_frame, corner_radius=6, fg_color=("gray85", "gray16"))
            row.pack(fill="x", pady=4, padx=5)
            ctk.CTkLabel(row, text=s_char, font=("Consolas", 16, "bold"), text_color="#2ECC71", width=30).pack(side="left", padx=(15, 5), pady=8)
            ctk.CTkLabel(row, text="➔", font=("Segoe UI", 12), text_color="gray").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=action, font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)
            ctk.CTkButton(row, text="✕", width=30, height=28, fg_color="transparent", text_color="#FF5252", hover_color="#421010", command=lambda c=s_char: self.delete_mapping(c)).pack(side="right", padx=10)

    def save_profile(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filepath:
            with open(filepath, 'w') as f: json.dump(self.key_map, f, indent=4)
            self.add_log(f"Profile saved: {filepath.split('/')[-1]}")

    def load_profile(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filepath:
            with open(filepath, 'r') as f: self.key_map = json.load(f)
            self.refresh_mapping_list()
            self.add_log(f"Profile loaded: {filepath.split('/')[-1]}")


class RadarVisualizerFrame(BaseSerialTool):
    def __init__(self, master):
        self.current_angle = 90
        self.sweep_direction = 1 
        self.max_distance = 50  
        self.blips = []
        super().__init__(master)
        self.after(50, self.update_radar_ui)  

    def build_custom_ui(self):
        # Inject custom slider into Connection Bar
        ctk.CTkLabel(self.conn_frame, text="Max Range:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(15, 5))
        self.range_var = ctk.IntVar(value=50)
        self.range_slider = ctk.CTkSlider(self.conn_frame, variable=self.range_var, from_=20, to=200, width=120, command=self.update_range)
        self.range_slider.pack(side="left", padx=5)
        self.range_val_label = ctk.CTkLabel(self.conn_frame, text="50 cm", font=("Consolas", 12), width=50, anchor="w")
        self.range_val_label.pack(side="left")

        # Radar Canvas Canvas
        self.canvas_width, self.canvas_height = 800, 400
        self.canvas = tk.Canvas(self.content_frame, bg="#0A0F0D", highlightthickness=0) 
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.canvas.bind("<Configure>", self.on_resize)

        # Bottom HUD overrides
        ctk.CTkLabel(self.active_display_frame, text="TRACKING STATUS", font=("Consolas", 12, "bold"), text_color="gray").pack(anchor="w")
        self.closest_tgt_lbl = ctk.CTkLabel(self.active_display_frame, text="CLEAR", font=("Consolas", 24, "bold"), text_color="#2ECC71")
        self.closest_tgt_lbl.pack(anchor="w", pady=(5, 0))
        self.tgt_count_lbl = ctk.CTkLabel(self.active_display_frame, text="Tracking: 0 Objects", font=("Consolas", 11), text_color="gray")
        self.tgt_count_lbl.pack(anchor="w")

    def handle_serial_data(self, data):
        """Called by BaseSerialTool thread when a string is received."""
        if "," in data:
            parts = data.split(",")
            if len(parts) == 2 and parts[0].lstrip('-').isdigit() and parts[1].lstrip('-').isdigit():
                angle, distance = int(parts[0]), int(parts[1])
                
                if angle != self.current_angle:
                    self.sweep_direction = 1 if angle > self.current_angle else -1
                self.current_angle = angle
                
                if 0 < distance <= self.max_distance:
                    # Calculate position natively
                    cx, cy = self.canvas_width / 2, self.canvas_height - 10
                    radius = min(self.canvas_width / 2, self.canvas_height) - 20
                    
                    if radius > 0:
                        rad = math.radians(angle)
                        scaled_dist = (distance / self.max_distance) * radius
                        target_x = cx + (scaled_dist * math.cos(rad))
                        target_y = cy - (scaled_dist * math.sin(rad))
                        
                        dist_pct = distance / self.max_distance
                        threat_color = "#FF5252" if dist_pct < 0.33 else ("#FFD700" if dist_pct < 0.66 else "#00E5FF")
                        
                        # Cluster Target logic
                        is_new_target = True
                        for blip in self.blips:
                            if abs(blip["angle"] - angle) <= 5 and abs(blip["raw_dist"] - distance) <= 5:
                                blip.update({"angle": angle, "raw_dist": distance, "dist_px": scaled_dist, "x": target_x, "y": target_y, "size": 8.0, "color": threat_color})
                                if blip["ripple_radius"] > 30: blip["ripple_radius"] = 0.0 
                                is_new_target = False
                                break

                        if is_new_target:
                            self.blips.append({"angle": angle, "raw_dist": distance, "dist_px": scaled_dist, "x": target_x, "y": target_y, "size": 8.0, "color": threat_color, "ripple_radius": 0.0})
                            self.after(0, self.add_log, f"Contact locked: {distance}cm ({angle}°)", dist_pct < 0.33)

    def on_stop(self):
        """Clear logic when system stops."""
        self.blips = []
        self.closest_tgt_lbl.configure(text="OFFLINE", text_color="gray")
        self.tgt_count_lbl.configure(text="Tracking: --")
        self.hud_frame.configure(border_color="#1E1E1E")

    def update_range(self, val):
        self.max_distance = int(val)
        self.range_val_label.configure(text=f"{self.max_distance} cm")
        self.draw_radar_background() 

    def on_resize(self, event):
        if event.width > 50 and event.height > 50:
            self.canvas_width, self.canvas_height = event.width, event.height
            self.draw_radar_background()

    def draw_radar_background(self):
        self.canvas.delete("grid")
        cx, cy = self.canvas_width / 2, self.canvas_height - 10
        radius = min(self.canvas_width / 2, self.canvas_height) - 20
        if radius <= 0: return

        for i in range(1, 4):
            r = radius * (i / 3)
            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=0, extent=180, style=tk.ARC, outline="#1E5128", dash=(4, 4), tags="grid")
            dist_val = int(self.max_distance * (i / 3))
            self.canvas.create_text(cx + 8, cy - r, text=f"{dist_val}cm", fill="#1E5128", font=("Consolas", 10), anchor="w", tags="grid")

        for angle in range(0, 181, 30):
            rad = math.radians(angle)
            self.canvas.create_line(cx, cy, cx + (radius * math.cos(rad)), cy - (radius * math.sin(rad)), fill="#1E5128", tags="grid")

    def update_radar_ui(self):
        """UI Render loop driven entirely by tkinter.after"""
        self.canvas.delete("dynamic")
        cx, cy = self.canvas_width / 2, self.canvas_height - 10
        radius = min(self.canvas_width / 2, self.canvas_height) - 20

        if radius > 0 and self.is_running:
            # Sweep Trail
            trail_colors = ["#2ECC71", "#229954", "#196F3D", "#114A29", "#0A2F1A"]
            for i in range(5):
                trail_ang = self.current_angle - (i * 3 * self.sweep_direction)
                if 0 <= trail_ang <= 180:
                    self.canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=trail_ang, extent=(3 * self.sweep_direction), style=tk.PIESLICE, fill=trail_colors[i], outline="", tags="dynamic")

            # Blip Processing
            alive_blips = []
            closest_dist = self.max_distance + 1
            has_critical = False

            for blip in self.blips:
                if blip["size"] > 0:
                    a, raw_dist, d_px = blip["angle"], blip["raw_dist"], blip["dist_px"]
                    x, y, size, color, ripple = blip["x"], blip["y"], blip["size"], blip["color"], blip["ripple_radius"]
                    
                    if raw_dist < closest_dist: closest_dist = raw_dist
                    if color == "#FF5252": has_critical = True

                    self.canvas.create_arc(cx - d_px, cy - d_px, cx + d_px, cy + d_px, start=a - 7.5, extent=15, style=tk.ARC, outline=color, width=size * 1.5, tags="dynamic")
                    
                    if size > 5:
                        self.canvas.create_line(x - 8, y, x + 8, y, fill="white", width=1, tags="dynamic")
                        self.canvas.create_line(x, y - 8, x, y + 8, fill="white", width=1, tags="dynamic")
                        txt_x, anchor = (x + 15, "w") if a > 90 else (x - 15, "e")
                        self.canvas.create_text(txt_x, y - 10, text=f"{raw_dist}cm", fill=color, font=("Consolas", 10, "bold"), anchor=anchor, tags="dynamic")

                    if size > 6: 
                        self.canvas.create_oval(x - ripple, y - ripple, x + ripple, y + ripple, outline=color, width=1, tags="dynamic")
                        blip["ripple_radius"] += 4 
                    
                    blip["size"] -= 0.15 
                    alive_blips.append(blip)

            self.blips = alive_blips

            # Update Bottom HUD
            self.tgt_count_lbl.configure(text=f"Tracking: {len(self.blips)} Objects")
            if closest_dist <= self.max_distance:
                threat_color = "#FF5252" if closest_dist < (self.max_distance * 0.33) else ("#FFD700" if closest_dist < (self.max_distance * 0.66) else "#00E5FF")
                self.closest_tgt_lbl.configure(text=f"TGT: {closest_dist}cm", text_color=threat_color)
            else:
                self.closest_tgt_lbl.configure(text="CLEAR", text_color="#2ECC71")

        self.after(30, self.update_radar_ui)

class SerialTranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Serial Toolbox")
        self.geometry("1000x750")
        self.minsize(950, 700)

        # Header Area
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(self.header_frame, text="Serial Toolbox", font=("Segoe UI", 28, "bold")).pack(side="left")
        ctk.CTkLabel(self.header_frame, text="Interactive Data Suite", font=("Segoe UI", 14), text_color="gray").pack(side="left", padx=(10, 0), pady=(10, 0))

        # Navigation
        self.current_view = ctk.StringVar(value="⌨️ Keyboard Mapper")
        self.view_selector = ctk.CTkSegmentedButton(self, values=["⌨️ Keyboard Mapper", "📡 Radar Visualizer"], variable=self.current_view, command=self.switch_view, font=("Segoe UI", 14, "bold"))
        self.view_selector.pack(fill="x", padx=20, pady=10)

        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self.frames = {
            "⌨️ Keyboard Mapper": KeyboardMapperFrame(self.main_container),
            "📡 Radar Visualizer": RadarVisualizerFrame(self.main_container)
        }
        self.active_frame = self.frames["⌨️ Keyboard Mapper"]
        self.active_frame.pack(fill="both", expand=True)

    def switch_view(self, view_name):
        if self.active_frame.is_running: 
            self.active_frame.stop_listening()
        self.active_frame.pack_forget()
        self.active_frame = self.frames[view_name]
        self.active_frame.pack(fill="both", expand=True)

    def on_closing(self):
        for frame in self.frames.values():
            if frame.is_running: 
                frame.stop_listening()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = SerialTranslatorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
