```markdown
# Serial2Radar: Arduino Object Visualizer

Serial2Radar is a Python-based GUI application that reads serial data from an Arduino radar project (using an HC-SR04 Ultrasonic Sensor and SG90 Servo) and visualizes the detected objects on a classic tactical radar screen in real-time.

## Features
- **Real-Time Visualization:** Smooth sweeping arm animation mapped to the servo's current angle.
- **Dynamic Blips:** Detected objects appear as blips on the radar and slowly fade out (phosphor decay simulation).
- **Auto-Port Detection:** Automatically scans and lists available COM ports.
- **Modern UI:** Built with `customtkinter` for a clean, dark-mode interface.

---

## 🛠️ Prerequisites
Before you begin, ensure you have the following installed on your computer:
* **Python 3.8 or higher** (Make sure to check "Add Python to PATH" during installation)
* Git (optional, for cloning the repository)

---

## 🚀 Installation & Setup

### 1. Clone the Repository
Download the code to your local machine:
```bash
git clone [https://github.com/bukanluq/Serial2Radar.git](https://github.com/bukanluq/Serial2Radar.git)
cd Serial2Radar
```

### 2. Create a Virtual Environment
It is highly recommended to use a virtual environment to keep dependencies isolated.
```bash
python -m venv venv
```

### 3. Activate the Virtual Environment
You must activate the environment every time you want to run the code.

* **Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate.bat
  ```
* **Windows (PowerShell):**
  ```powershell
  venv\Scripts\Activate.ps1
  ```
* **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```
*(When activated, you will see `(venv)` at the beginning of your terminal line).*

### 4. Install Dependencies
Install the required Python libraries using `pip`. 

If you have a `requirements.txt` file, run:
```bash
pip install -r requirements.txt
```

*(If you don't have a requirements file yet, install them manually and save them):*
```bash
pip install customtkinter pyserial
pip freeze > requirements.txt
```

---

## 💻 How to Run

1. Ensure your Arduino is plugged in and running the correct radar code.
2. Ensure the **Arduino IDE Serial Monitor is CLOSED** (Otherwise, the Python app cannot access the COM port).
3. Run the Python script:
```bash
python main.py
```
*(Replace `main.py` with whatever you named your Python file, e.g., `serial2radar.py`)*

4. In the application GUI:
   * Select your Arduino's **COM Port**.
   * Set the Baud Rate to **115200**.
   * Click **START RADAR**.

---

## 🔌 Arduino Data Format
For this software to work, your Arduino **must** send data to the Serial Monitor in a strict CSV (Comma-Separated Values) format at a baud rate of `115200`.

**Expected Output:**
`Angle,Distance`

**Example Arduino Loop:**
```cpp
Serial.print(currentAngle);
Serial.print(",");
Serial.println(distance);
```

---

## ⚠️ Troubleshooting

* **Error: Access Denied / Port In Use:** You left the Serial Monitor open in the Arduino IDE. Close it and click "START RADAR" again.
* **No UI appears or missing module error:** You likely forgot to activate your virtual environment before running the script. Run the activation command from Step 3.
* **Canvas looks glitchy on resize:** The software dynamically redraws the radar grid. Just release the mouse after resizing the window and it will snap into place.
