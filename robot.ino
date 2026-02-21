#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

const char* ssid = "";
const char* password = "";

Servo baseServo, shoulderServo, elbowServo, wristServo;
const int laserPin = 23;
WebServer server(80);

int basePos = 90, shoulderPos = 90, elbowPos = 90, wristPos = 90;
bool laserOn = false;

void setup() {
  Serial.begin(115200);
  
  baseServo.attach(18);
  shoulderServo.attach(19);
  elbowServo.attach(21);
  wristServo.attach(22);
  
  pinMode(laserPin, OUTPUT);
  digitalWrite(laserPin, LOW);
  
  pinMode(12, OUTPUT); pinMode(13, OUTPUT); pinMode(14, OUTPUT);
  pinMode(15, OUTPUT); pinMode(2, OUTPUT); pinMode(4, OUTPUT);
  
  baseServo.write(90); shoulderServo.write(90); elbowServo.write(90); wristServo.write(90);
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(1000);
  
  server.on("/coord", HTTP_POST, [](){
    if (server.hasArg("plain")) {
      String cmd = server.arg("plain");
      int x = cmd.substring(0, cmd.indexOf(',')).toInt();
      int y = cmd.substring(cmd.indexOf(',')+1).toInt();
      
      basePos = map(x, 0, 320, 45, 135);  
      shoulderPos = map(y, 0, 240, 45, 135);
      
      basePos = constrain(basePos, 0, 180);
      shoulderPos = constrain(shoulderPos, 0, 180);
      
      baseServo.write(basePos);
      shoulderServo.write(shoulderPos);
      
      server.send(200, "text/plain", "X"+String(x)+"Y"+String(y)+"->B"+String(basePos)+"S"+String(shoulderPos));
    } else server.send(400, "text/plain", "Error");
  });
  
  server.on("/laser", HTTP_POST, [](){
    laserOn = !laserOn;
    digitalWrite(laserPin, laserOn);
    server.send(200, "text/plain", laserOn ? "ON" : "OFF");
  });
  
  server.on("/wheels", HTTP_POST, [](){
    String cmd = server.arg("plain");
    int speed = cmd.length() > 1 ? constrain(cmd.substring(1).toInt(), 0, 255) : 0;
    char dir = cmd.charAt(0);
    
    analogWrite(14, 0); analogWrite(2, 0);
    
    if (dir == 'F') {
      analogWrite(14, speed); digitalWrite(12, HIGH); digitalWrite(13, LOW);
      analogWrite(2, speed); digitalWrite(15, HIGH); digitalWrite(4, LOW);
    } else if (dir == 'B') {
      analogWrite(14, speed); digitalWrite(12, LOW); digitalWrite(13, HIGH);
      analogWrite(2, speed); digitalWrite(15, LOW); digitalWrite(4, HIGH);
    } else if (dir == 'L') {
      analogWrite(14, speed/2); digitalWrite(12, LOW); digitalWrite(13, HIGH);
      analogWrite(2, speed); digitalWrite(15, HIGH); digitalWrite(4, LOW);
    } else if (dir == 'R') {
      analogWrite(14, speed); digitalWrite(12, HIGH); digitalWrite(13, LOW);
      analogWrite(2, speed/2); digitalWrite(15, LOW); digitalWrite(4, HIGH);
    }
    server.send(200, "text/plain", cmd);
  });
  
  server.begin();
}

void loop() {
  server.handleClient();
}
