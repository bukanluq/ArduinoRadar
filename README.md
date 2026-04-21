## 🛠️ Requirements

Make sure the following are installed before starting

- Python 3.8 or higher  

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/bukanluq/ArduinoRadar.git
cd ArduinoRadar
````

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows Command Prompt**

```cmd
venv\Scripts\activate.bat
```

**Windows PowerShell**

```powershell
venv\Scripts\Activate.ps1
```

**macOS or Linux**

```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal when activated.

---

### 4. Install dependencies

If `requirements.txt` exists

```bash
pip install -r requirements.txt
```

If not, install manually

```bash
pip install customtkinter pyserial
pip freeze > requirements.txt
```

---

## ▶️ Running the Application

1. Connect your Arduino and upload the radar sketch
2. Make sure the Arduino Serial Monitor is closed
3. Run the application

```bash
python main.py
```

*(Replace `main.py` with your actual file name if different)*

4. Inside the app

   * Select the correct COM port
   * Set baud rate to `115200`
   * Click **START RADAR**

---

## 🔌 Arduino Data Format

The Arduino must send serial data in this exact format

```
Angle,Distance
```

### Example

```
90,25
```

### Sample Arduino code

```cpp
Serial.print(currentAngle);
Serial.print(",");
Serial.println(distance);
```

---

## ⚠️ Troubleshooting

**Port in use or access denied**
Close the Arduino Serial Monitor. Only one program can use the port at a time.

**Module not found or app not launching**
Activate the virtual environment before running the script.

**UI glitches when resizing**
The radar canvas redraws dynamically. Release the window after resizing to refresh properly.

---

## 📌 Notes

* Recommended baud rate is `115200`
* Works best with stable serial output timing from Arduino
* Designed for HC-SR04 and SG90 based radar setups

---

## 📷 Preview


