import serial
import time
import settings as S

def t():
    """time """
    return time.strftime("%H:%M:%S", 
             time.gmtime(time.time()))


class FormatError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class TimeoutError(Exception):
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
class Transmiter:
    SERIAL_PORT = "COM14"
    BAUDRATE = 115200
    RESPONSE_TIMEOUT_S = 100 # it can take long to travel long distance

    def __init__(self, console:bool, port=SERIAL_PORT, baudrate=BAUDRATE):
        self.SERIAL_PORT = port
        self.BAUDRATE = baudrate

        self.console_mode = console

        # open the serial connection
        self.ser = serial.Serial(self.SERIAL_PORT, self.BAUDRATE, timeout=1)

        time.sleep(1)    # short delay to let the port settle

        pico_ret = self.send_and_receive("SCM " + str(int(console)) + '\n')
        print(f"pico consoleMode: {console}, returned: {pico_ret}")

    def send_and_receive(self, message:str|None) -> bool: 
        """
        0 = all good;
        1 = error;
        2 = timeout
        """

        if message is not None: # allow empty messages for only waiting for responce    
            #check weter the message contains '\n'
            if not S.SPEED_MODE:
                if list(message)[-1] != '\n':
                    raise FormatError("message: " + message + " is missing a '\n'")
                
            self.ser.write(message.encode("utf-8")) # send encoded byte message
            
        start_time = time.time()

        #wait for response
        while True:# wait for responce indefinetly add time out
            #either 0 or 1 or ""
            response = self.ser.readline().decode().strip()
            
            if response != "": # resturn pth 1, 0, string

                if not S.SPEED_MODE: # check weter the response can be converted to a bool
                    if not response.isdigit():
                        raise ReturnError("response: '" + response + "' is not a integer")
                    
                    else:
                        int_response = int(response)
                        if not int_response in [0, 1]:
                            raise ReturnError("response: '" + str(int_response) + "' is not between 0 and 1 -> can't be converted to bool")
                        
                        else:
                            return bool(int_response)
                
                return bool(int(response))
            
            if time.time() - start_time >= Transmiter.RESPONSE_TIMEOUT_S:
                raise TimeoutError("responce not recived in last " + str(Transmiter.RESPONSE_TIMEOUT_S) + " s")
    
    
    def console(self):
        """stream of returned values"""

        if not self.console_mode:
            raise ConsoleError("pico isnt in console Mode")
        
        print("Pico Console: ")
        while True:
            pico_ret = self.send_and_receive(None) 
            print(str(t()) + ": " + str(pico_ret))


    def __deinit__(self):
        self.ser.close()
