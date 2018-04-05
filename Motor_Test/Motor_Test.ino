#include <Servo.h>

Servo intake;
Servo shooter;

int pos = 0;

byte servoPin = 8;
byte servoMin = 10;
byte servoMax = 170;
byte servoPos = 0;
byte newServoPos = servoMin;

const byte buffSize = 40;
char inputBuffer[buffSize];
const char startMarker = '<';
const char endMarker = '>';
byte bytesRecvd = 0;
boolean readInProgress = false;
boolean newDataFromPC = false;

char messageFromPC[buffSize] = {0};
int newFlashInterval = 0;
float servoFraction = 0.0; // fraction of servo range to move

unsigned long curMillis;

int intakePos;
int shooterPos;

void setup() {
  intake.attach(2);
  shooter.attach(3);

  Serial.begin(9600);
  Serial.print("<Arduino Connected...>");
}

void loop() {
  curMillis = millis();
  getDataFromPC();
//  updateFlashInterval();
//  updateServoPos();
  replyToPC();
//  flashLEDs();
//  moveServo();
}

void getDataFromPC() {    
  if(Serial.available() > 0) {
    char x = Serial.read(); 
       
    if (x == endMarker) {
      readInProgress = false;
      newDataFromPC = true;
      inputBuffer[bytesRecvd] = 0;
      parseData();
    }
    
    if(readInProgress) {
      inputBuffer[bytesRecvd] = x;
      bytesRecvd ++;
      if (bytesRecvd == buffSize) {
        bytesRecvd = buffSize - 1;
      }
    }

    if (x == startMarker) { 
      bytesRecvd = 0; 
      readInProgress = true;
    }
  }
}

void parseData() {
  char * strtokIndx; // this is used by strtok() as an index

  strtokIndx = strtok(inputBuffer, ",");
  maxSpeed = atof(strtokIndex);  //Max Motor Speed -> MAX SPEED
  
  strtokIndx = strtok(NULL,",");
//  Serial.println(strtokIndx);  //Debug
  intakePos = map(atoi(strtokIndx), -1, 1, 1000, 2000);
//  Serial.println(intakePos);  //Debug
  intake.writeMicroseconds(intakePos * maxSpeed);  //Joy1 Y -> INTAKE

  strtokIndx = strtok(NULL, ",");  //Joy2 X
 
  strtokIndx = strtok(NULL, ",");
  shooterPos = map(atoi(strtokIndx), -1, 1, 1000, 2000);
  shooter.writeMicroseconds(shooterPos * maxSpeed * -1);  //Joy2 Y -> SHOOTER
}

void replyToPC() {

  if (newDataFromPC) {
    newDataFromPC = false;
    Serial.print("<Intake Speed ");
    Serial.print(intakePos);
    Serial.print(" Shooter Speed ");
    Serial.print(shooterPos);
    Serial.println(">");
  }
}
