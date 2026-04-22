Before getting started, ensure you have:

- Python 3.8 or higher installed

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/bukanluq/ArduinoRadar.git
cd ArduinoRadar
````

---

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

---

### 3. Activate the Environment

**Windows (Command Prompt)**

```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell)**

```powershell
venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source venv/bin/activate
```

Once activated, you should see `(venv)` in your terminal.

---

### 4. Install Dependencies

If a `requirements.txt` file exists:

```bash
pip install -r requirements.txt
```

Otherwise, install manually:

```bash
pip install customtkinter pyserial
pip freeze > requirements.txt
```

---

## ▶️ Running the Application

1. Connect your Arduino and upload the radar sketch
2. Ensure the Arduino Serial Monitor is **closed**
3. Run the application:

```bash
python main.py
```

> Replace `main.py` with your actual entry file if different.

4. Inside the application:

   * Select the correct COM port
   * Set the baud rate to `115200`
   * Click **START RADAR**

---

## 🔌 Arduino Data Format

The Arduino must send serial data in the following format:

```
Angle,Distance
```

### Example

```
90,25
```

### Sample Arduino Code

```cpp
Serial.print(currentAngle);
Serial.print(",");
Serial.println(distance);
```

---

## ⚠️ Troubleshooting

**Port in use / Access denied**
Close the Arduino Serial Monitor. Only one application can access the serial port at a time.

**Module not found / App not launching**
Ensure the virtual environment is activated before running the script.

**UI glitches during resizing**
The radar canvas redraws dynamically. Resize and release the window to refresh properly.

---

## 📌 Notes

* Recommended baud rate: `115200`
* Works best with stable serial output timing
* Designed for HC-SR04 and SG90-based radar setups

---

## 📷 Preview

<img width="1366" height="721" alt="Radar Preview" src="https://github.com/user-attachments/assets/104a8622-9ff7-41e1-9a2d-75f4a1f98fa3" />

---

## 📦 Downloads

Get the latest prebuilt version for your platform:

* **Windows (Recommended)**
  [https://nightly.link/bukanluq/ArduinoRadar/workflows/build/main/SerialTranslator-Windows-Nightly.zip](https://nightly.link/bukanluq/ArduinoRadar/workflows/build/main/SerialTranslator-Windows-Nightly.zip)

* **Linux (x64)**
  [https://nightly.link/bukanluq/ArduinoRadar/workflows/build/main/SerialTranslator-Linux-x64-Nightly.zip](https://nightly.link/bukanluq/ArduinoRadar/workflows/build/main/SerialTranslator-Linux-x64-Nightly.zip)

* **macOS (Apple Silicon)**
  [https://nightly.link/bukanluq/ArduinoRadar/workflows/build/main/SerialTranslator-macOS-AppleSilicon-Nightly.zip](https://nightly.link/bukanluq/ArduinoRadar/workflows/build/main/SerialTranslator-macOS-AppleSilicon-Nightly.zip)

* **macOS (Intel)**
  [https://nightly.link/bukanluq/ArduinoRadar/workflows/build/main/SerialTranslator-macOS-Intel-Nightly.zip](https://nightly.link/bukanluq/ArduinoRadar/workflows/build/main/SerialTranslator-macOS-Intel-Nightly.zip)
