import serial

SERIAL_PORT = 'COM3'  # Update to the correct port
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Serial connection established.")
    while True:
        data = ser.readline().decode('utf-8').strip()
        if data:
            print(f"Received: {data}")
except Exception as e:
    print(f"Error: {e}")
