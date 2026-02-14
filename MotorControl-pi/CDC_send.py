import serial
import time

# replace with your Pico’s serial port name;
# on Linux it might be "/dev/ttyACM0" or similar
# on Windows something like "COM3"
SERIAL_PORT = "COM14"
BAUDRATE = 115200

# open the serial connection
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

time.sleep(2)    # short delay to let the port settle
ser.write(67)
    
# send a line to the Pico
try:
    while True:

        line_raw = ser.readline()
        line = line_raw.decode().strip()
        if line != "Got char:" and line != "":
            print(line)
        time.sleep(.01)
finally:
    ser.close()
    exit()
