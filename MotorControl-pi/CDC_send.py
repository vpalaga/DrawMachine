import serial
import serial.tools.list_ports
import time
import settings as s

def t():
    """time """
    return time.strftime("%H:%M:%S", 
             time.gmtime(time.time()))


class FormatError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class PicoTimeoutError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ReturnError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ConsoleError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

# replace with your Pico’s serial port name;
# on Linux it might be "/dev/ttyACM0" or similar
# on Windows something like "COM3"

def r(m:bool|str)->str:
    if isinstance(m, bool):
        if not m:
            return "OK"
        return "ERROR"
    return m

def find_pico_serial_port():
    print("searching for pico...")
    for port in serial.tools.list_ports.comports():
        if "2E8A" in port.hwid:  # Raspberry Pi VID
            return port.device
    raise PicoTimeoutError("ERROR: can't find Pico on any serial ports")

class Transmitter:
    SERIAL_PORT = find_pico_serial_port()
    BAUDRATE = 115200
    RESPONSE_TIMEOUT_S = 200 # it can take a long time to travel long distance

    def __init__(self, console:bool, port=SERIAL_PORT, baudrate=BAUDRATE):
        self.SERIAL_PORT = port
        self.BAUDRATE = baudrate

        self.console_mode = console

        # open the serial connection
        print(f"OK: connecting to Pico on {Transmitter.SERIAL_PORT}...")
        self.ser = serial.Serial(self.SERIAL_PORT, self.BAUDRATE, timeout=1)

        time.sleep(1)    # short delay to let the port settle
        print(f"OK: successfully connected")
        # set pico console mode
        pico_receive = self.send_and_receive("SCM " + str(int(console)) + '\n')
        print(f"OK: pico consoleMode: {console}, returned: {r(pico_receive)}")

        # wait for response
        pico_finish = self.send_and_receive(None)
        print(f"OK: pico consoleMode: {console}, finished: {r(pico_finish)}")

    def send_and_receive(self, message:str|None) -> bool|str: 
        """
        0 = all good;
        1 = error;
        2 = timeout
        """

        if message is not None: # allow empty messages for only waiting for response

            #check whether the message contains '\n'
            if list(message)[-1] != '\n':
                raise FormatError("message: " + message + " is missing a '\n'")

            self.ser.write(message.encode("utf-8")) # send encoded byte message
            
        start_time = time.time()

        #wait for response
        while True:# wait for response indefinitely add time out
            #either 0 or 1 or ""
            response = self.ser.readline().decode().strip()
            
            if response != "": # return pth 1, 0, string
                
                if self.console_mode:
                    return response

                if not s.SPEED_MODE: # check whether the response can be converted to a bool
                    if not response.isdigit():
                        raise ReturnError("response: '" + response + "' is not a integer")
                    
                    else:
                        int_response = int(response)
                        if not int_response in [0, 1]:
                            raise ReturnError("response: '" + str(int_response) + "' is not between 0 and 1 -> can't be converted to bool")
                        
                        else:
                            return bool(int_response)
                
                return bool(int(response))
            
            if time.time() - start_time >= Transmitter.RESPONSE_TIMEOUT_S:
                raise PicoTimeoutError("response not received in last " + str(Transmitter.RESPONSE_TIMEOUT_S) + " s")
    
    
    def console(self):
        """stream of returned values"""

        if not self.console_mode:
            raise ConsoleError("pico isn't in console Mode")

        print("OK: Pico Console: ")
        while True:
            pico_ret = self.send_and_receive(None) 
            print(str(t()) + ": " + str(pico_ret))


    def __deinit__(self):
        print(f"OK: closing serial port: {Transmitter.SERIAL_PORT}")
        self.ser.close()
