#include <Servo.h>

Servo servo;

// Pins
const int joyX = A0, joyY = A1, btn = 3;
const int trig = 5, echo = 6, servoPin = 9;

// State
int cx, cy, angle = 90;

int getDistance() {
  digitalWrite(trig, LOW); delayMicroseconds(2);
  digitalWrite(trig, HIGH); delayMicroseconds(10);
  digitalWrite(trig, LOW);

  long d = pulseIn(echo, HIGH, 30000);
  return d ? d * 0.034 / 2 : 0;
}

void setup() {
  Serial.begin(115200);

  servo.attach(servoPin);
  servo.write(angle);

  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);
  pinMode(btn, INPUT_PULLUP);

  delay(500);
  cx = analogRead(joyX);
  cy = analogRead(joyY);
}

void loop() {
  int x = analogRead(joyX) - cx;
  int y = analogRead(joyY) - cy;

  if (abs(x) < 20) x = 0;
  if (abs(y) < 20) y = 0;

  char c = (!digitalRead(btn)) ? ' ' :
           (x > 300 && abs(y) < 200) ? 'W' :
           (x < -300 && abs(y) < 200) ? 'S' :
           (y > 300 && abs(x) < 200) ? 'D' :
           (y < -300 && abs(x) < 200) ? 'A' : 'I';

  if (c == 'A' && angle < 180) angle += 2;
  if (c == 'D' && angle > 0)   angle -= 2;

  servo.write(angle);
  delay(30);

  int dist = getDistance();

  Serial.print(angle);
  Serial.print(",");
  Serial.println(dist);

  delay(20);
}
