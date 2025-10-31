import serial
import time

# Serial connection settings
SERIAL_PORT = "COM4"  # Change this based on your device port
BAUD_RATE = 115200
TIMEOUT = 1  # in seconds

# Command codes
STX = 0x02
ETX = 0x03
COMMANDS = {
    "ANALOG_READ": [0xAE, 0x09],  # Read all analog inputs
    "PORT_WRITE": [0xBF, 0xBB, 0x3F],
    "DDR_SET": [0xDD, 0xBB, 0x3F],
    "PWM_WRITE": [0xE4, 0x09, 128],  # Set PWM on pin 9 to a medium value
    "PIN_READ": [0xFE, 0xCC]  # Read all digital ports
}

def send_command(ser, command_name, command_data):
    """Send a command to Arduino and receive the response"""
    packet = [STX] + command_data + [ETX]
    ser.write(bytearray(packet))
    ser.flush()
    
    time.sleep(0.1)  # Wait for data reception
    response = ser.read_all()
    return response

def parse_response(response):
    """Parse the received response"""
    if len(response) < 3 or response[0] != STX or response[-1] != ETX:
        return "Error: Invalid response"
    
    data = list(response[1:-1])  # Remove STX and ETX
    if data[0] == 0xEE:
        return f"Error: Code {hex(data[1])}, Details: {hex(data[2])}"
    
    return f"Parsed Data: {data}"

if __name__ == "__main__":
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        time.sleep(2)  # Wait for connection to stabilize
        
        for name, cmd in COMMANDS.items():
            print(f"\nSending command: {name}")
            response = send_command(ser, name, cmd)
            print(f"Raw response: {response}")
            print(f"Parsed response: {parse_response(response)}")
        
        ser.close()
    except Exception as e:
        print(f"An error occurred: {e}")
