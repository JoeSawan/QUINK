#include <Arduino.h>
#include <avr/pgmspace.h>

// ------ Protocol Constants ------
#define STX 0xEB
#define ETX 0xEE
#define BUFFER_SIZE 32
#define MAX_PARAMS 2
#define PACKET_TIMEOUT_MS 100

unsigned long lastByteTime = 0;
byte inputBuffer[BUFFER_SIZE];
byte bufferIndex = 0;
bool packetStarted = false;

// Command Codes
enum {
  CMD_ANALOG_READ = 0xAE,
  CMD_PORT_WRITE = 0xBF,
  CMD_DDR_SET = 0xDD,
  CMD_PWM_WRITE = 0xE4,
  CMD_PIN_READ = 0xFE
};

// Error Codes
enum {
  ERR_INVALID_CMD = 0xE1,
  ERR_BAD_PARAM = 0xE2,
  ERR_PIN_RANGE = 0xE3,
  ERR_PORT_RANGE = 0xE4,
  ERR_PWM_NOT_SUPP = 0xE5,
  ERR_BUFFER_OVERFLOW = 0xE6
};

const byte pwmPins[] PROGMEM = {3, 5, 6, 9, 10, 11};

void setup() {
  Serial.begin(115200);
}

void loop() {
  receivePacket();
}

// ------ Packet Reception ------
void receivePacket() {
  while (Serial.available() > 0) {
    byte inByte = Serial.read();
    lastByteTime = millis();

    if (inByte == STX) {
      bufferIndex = 0;
      packetStarted = true;
    } else if (inByte == ETX && packetStarted) {
      processPacket(inputBuffer, bufferIndex);
      packetStarted = false;
    } else if (packetStarted) {
      if (bufferIndex < BUFFER_SIZE) {
        inputBuffer[bufferIndex++] = inByte;
      } else {
        sendError(ERR_BUFFER_OVERFLOW);
        packetStarted = false;
      }
    }
  }
  
  if (packetStarted && (millis() - lastByteTime > PACKET_TIMEOUT_MS)) {
    packetStarted = false;
    bufferIndex = 0;
  }
}

// ------ Command Processing ------
void processPacket(byte *data, byte length) {
  if (length < 1) {
    sendError(ERR_INVALID_CMD);
    return;
  }

  byte command = data[0];
  byte params[MAX_PARAMS] = {0};
  
  for (byte i = 1; i < length && (i-1) < MAX_PARAMS; i++) {
    params[i-1] = data[i];
  }

  switch (command) {
    case CMD_ANALOG_READ:
      handleAnalogRead(params[0]);
      break;
      
    case CMD_PORT_WRITE:
      if (length == 3) handlePortWrite(params[0], params[1]);
      else sendError(ERR_BAD_PARAM);
      break;
      
    case CMD_DDR_SET:
      if (length == 3) handleDDRSet(params[0], params[1]);
      else sendError(ERR_BAD_PARAM);
      break;
      
    case CMD_PWM_WRITE:
      if (length == 3) handlePWMWrite(params[0], params[1]);
      else sendError(ERR_BAD_PARAM);
      break;
      
    case CMD_PIN_READ:
      if (length == 2) handlePinRead(params[0]);
      else sendError(ERR_BAD_PARAM);
      break;
      
    default:
      sendError(ERR_INVALID_CMD);
  }
}

// ------ Analog Read Handler ------
void handleAnalogRead(byte pin) {
  if (pin == 0xAA) { // Read all analog pins
    byte response[17] = {CMD_ANALOG_READ};
    for (byte i = 0; i < 8; i++) {
      int val = analogRead(i);
      response[i*2 + 1] = highByte(val);
      response[i*2 + 2] = lowByte(val);
    }
    sendPacket(response, sizeof(response));
  }
  else if (pin <= 7) { // Single pin read
    int val = analogRead(pin);
    byte response[] = {CMD_ANALOG_READ, pin, highByte(val), lowByte(val)};
    sendPacket(response, sizeof(response));
  }
  else {
    sendError(ERR_PIN_RANGE);
  }
}

// ------ Error Handling ------
void sendError(byte errorCode) {
  byte errorPacket[] = {STX, errorCode, ETX};
  Serial.write(errorPacket, sizeof(errorPacket));
  Serial.flush();
}

// ------ Other Handlers (بقية الدوال بنفس الهيكل السابق مع تعديلات بسيطة) ------
void handlePortWrite(byte port, byte value) {
  switch (port) {
    case 0xBB: PORTB = value & 0x3F; break;
    case 0xCC: PORTC = value & 0x3F; break;
    case 0xDD: PORTD = value & 0xFC; break;
    default: sendError(ERR_PORT_RANGE); return;
  }
  byte response[] = {STX, CMD_PORT_WRITE, port, value, ETX};
  Serial.write(response, sizeof(response));
}

void sendPacket(byte *data, byte length) {
  Serial.write(STX);
  Serial.write(data, length);
  Serial.write(ETX);
  Serial.flush();
}

void handleDDRSet(byte port, byte mode) {
  switch (port) {
    case 0xBB: DDRB = mode & 0x3F; break;
    case 0xCC: DDRC = mode & 0x3F; break;
    case 0xDD: DDRD = mode & 0xFC; break;
    default: sendError(ERR_PORT_RANGE); return;
  }
  byte response[] = {CMD_DDR_SET, port, mode};
  sendPacket(response, sizeof(response));
}

void handlePWMWrite(byte pin, byte value) {
  bool validPin = false;
  for (byte i = 0; i < sizeof(pwmPins); i++) {
    if (pin == pgm_read_byte(&pwmPins[i])) {
      validPin = true;
      break;
    }
  }
  if (!validPin) {
    sendError(ERR_PWM_NOT_SUPP);
    return;
  }
  analogWrite(pin, value);
  byte response[] = {CMD_PWM_WRITE, pin, value};
  sendPacket(response, sizeof(response));
}

void handlePinRead(byte port) {
  byte value;
  switch (port) {
    case 0xBB: value = PINB; break;
    case 0xCC: value = PINC; break;
    case 0xDD: value = PIND; break;
    default: sendError(ERR_PORT_RANGE); return;
  }
  byte response[] = {CMD_PIN_READ, port, value};
  sendPacket(response, sizeof(response));
}