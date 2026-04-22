#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

// Initialize LCD (Address 0x27 is standard, change to 0x3F if your screen is blank)
LiquidCrystal_I2C lcd(0x27, 16, 2); 
Servo radarServo;

// Pin Definitions
const int joyX = A0;
const int joyY = A1;
const int btnPin = 3;
const int trigPin = 5;
const int echoPin = 6;
const int servoPin = 9;

// Global Variables
int centerX, centerY;
int currentAngle = 90; // Start looking straight ahead

void setup() {
  // Must match the Python script baud rate
  Serial.begin(115200); 
  
  // Setup LCD
  lcd.init();
  lcd.backlight();
  
  // Setup Servo
  radarServo.attach(servoPin);
  radarServo.write(currentAngle);
  
  // Setup Sensor & Button Pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(btnPin, INPUT_PULLUP);
  
  // Joystick Calibration
  delay(500);
  centerX = analogRead(joyX);
  centerY = analogRead(joyY);
  
  lcd.setCursor(0, 0);
  lcd.print("Radar Online");
  delay(1000);
  lcd.clear();
}

// Custom function to handle distance math
int getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // 30000 microsecond timeout prevents the code from freezing if no object is found
  long duration = pulseIn(echoPin, HIGH, 30000); 
  
  if (duration == 0) return 0; // Return 0 if out of range
  return duration * 0.034 / 2;
}

void loop() {
  // --- 1. JOYSTICK LOGIC ---
  int x = analogRead(joyX) - centerX;
  int y = analogRead(joyY) - centerY;
  if (abs(x) < 20) x = 0; 
  if (abs(y) < 20) y = 0;

  char curr = 'I';

  if (!digitalRead(btnPin)) curr = ' '; // Space
  else if (x >= 300 && abs(y) <= 200) curr = 'W';
  else if (x <= -300 && abs(y) <= 200) curr = 'S';
  else if (y >= 300 && abs(x) <= 200) curr = 'D';
  else if (y <= -300 && abs(x) <= 200) curr = 'A';

  // --- 2. SERVO CONTROL ---
  // If pushing Left (A), increase angle. If Right (D), decrease. 
  // Swap the += and -= if your physical servo moves the wrong way.
  if (curr == 'A' && currentAngle < 180) {
    currentAngle += 2; 
  } 
  else if (curr == 'D' && currentAngle > 0) {
    currentAngle -= 2;
  }
  radarServo.write(currentAngle);

  // ==========================================
  // FIX APPLIED HERE
  // Give the servo 30ms to physically reach the angle and stop vibrating.
  // This prevents the ultrasonic sound wave from smearing across the room.
  // ==========================================
  delay(30); 

  // --- 3. SENSOR READING ---
  int distance = getDistance();

  // --- 4. DATA OUTPUT FOR PYTHON ---
  // Prints strictly: Angle,Distance (e.g., 90,15)
  Serial.print(currentAngle);
  Serial.print(",");
  Serial.println(distance);

  // --- 5. LCD DISPLAY UPDATE ---
  lcd.setCursor(0, 0);
  lcd.print("Angle: "); 
  lcd.print(currentAngle); 
  lcd.print(" deg  "); // Extra spaces overwrite old leftover characters
  
  lcd.setCursor(0, 1);
  lcd.print("Dist:  "); 
  lcd.print(distance); 
  lcd.print(" cm   ");

  delay(20); // Stability delay to prevent overwhelming the serial port
}
