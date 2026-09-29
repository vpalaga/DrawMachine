# Draw Machine by VPalaga 

The idea is to make a plotter.

 The FCODE is my own simplification of .gcode protocol. I maight implememnt the .gcode later for the sake of my own sanity, but for now I am working with my own fuck creation - FCODE.

**The Goal: 100% working reliable x, y potter to do my homework.** 

>Partially based on Scrabble bot.
---

## .FCODE (quite old examples, they are not accurate at all <3)
>**FCODE Generation example in `FCODEgenerator/useExample.py`**  

``` python
from FCODEgenerator.main import FGenerator

# create a generatin object
gen = FGenerator("train_v1.dxf", acc=.1, vis_scale=10, text=False)

# generate the FCODE from the provided dxf file
gen.generate_instructions()
 # the save format / location can be configured under gen.py method: save()
gen.save()
```

Payload from Pi to Pico examples (FCODE):
```
CALIBRATE
MOVE 45.478 3.671
PENUP
MOVE 67.092 89.082
PENDOWN 
```
| Function | Arguments | Description |
| -------- | --------- | ----------- |
| MOVE | 2 | move the head to the x, y position| 
| WAIT | 1 |wait *x* seconds |
| CALIBRATE | 0 | calibrate the head (using the swiches at 0, 0) |
| *PENUP* | 0 | set the pen positon to be up |
| *PENDOWN* | 0 | set the pen position to be down|   

> Current functions: (can be found under `FCODEgenerator.segmentFunctions.Instruction.instructions_parameters_len.keys()`

---
## Raspberry Pi
*Python on Raspberry Pi 4B*   
+ file reading
+ run `MotorControl`
+ send float x, y coordinates to Raspberry Pico 2W
+ control servo on the head (*depending on the current use*) or head in general (PCA PCB)
+ > maybe even web server host for FCODE upload or remote stearing 



> To implement multifunctions, the Inscructions need to have be adjusted to the new argument length 
---
## Raspberry Pico  
Microcontroller running the main `c` loop, basicaly the PICO is just a dual simultanious stepper driver: 
+ recive functions
+ respond with error/confirmantion messages (CDC)
+ drive the end swiches (draw current when closed)
+ Send logic to x, y TMC 2209 Drivers

I am using **Raspberry Pi Pico VS Code extension** to write, compile and upload the code to my Pico.

---
### The idea for the c++ code running on the pico:
USB CDC Virtual Serial data exchange, to send `MOVE` coordinates to the pico.

> CDC Example
``` cpp
// Pico: client
while (true) {
        if (stdio_usb_connected(w)) {
            // read a char if available
            int c = getchar_timeout_us(0);

            if (c >= 0) {
                printf("Got char: %c\n", (char)c);
            }
        }
        sleep_ms(10);
    }
```
> install Python lib `pyserial`
``` python
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
ser.write(b"hello world!") # make shure you send the tring in byte type
    
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
```
### Stepping

Stepps moves are computed by Bresenham move function

![./images/Bresenham-style move function.png](https://github.com/vpalaga/DrawMachine/blob/master/images/Bresenham-style%20move%20function.png)

```cpp
class StepperDriver{
public:
    Stepper xStepperMotor;
    Stepper yStepperMotor;

    StepperDriver()
        : xStepperMotor(X_STP_STEPPER_PIN, X_DIR_STEPPER_PIN, 100),
          yStepperMotor(Y_STP_STEPPER_PIN, Y_DIR_STEPPER_PIN, 100) {
    }
    void bresenham(Stepper leadStepper, Stepper followStepper, int lead, int follow, bool leadDir, bool followDir){
        // how many steps of follow pro one step of lead
        float bresenhamStep = (float)follow / lead; // needs to be <0 

        int followPos   = 0;
        int followCycle;
        int diffFollowCycle;

        for (int cycle = 1; cycle<lead+1; cycle++){ // cycle need to start at 1
            
            // calculate how many steps at current cycle position 
            followCycle = round(cycle*bresenhamStep);
            
            // check how many are needed for this cycle
            diffFollowCycle = followCycle - followPos;

            // update the followPos to current follow position
            followPos += diffFollowCycle;

            //move the steppers accordingly
            // step: bool: dir, int steps, microseconds_sleep
            leadStepper.step(leadDir,1,100);
            followStepper.step(followDir,diffFollowCycle,100); // move the follow if needed
        }
    }

    void move(int x, int y){

        bool x_dir = (x<0) ? false : true; // change if the direction is wrong
        bool y_dir = (y<0) ? false : true;

        // set both to positive
        x = abs(x); y = abs(y);

        if (x >= y){ // x = lead
            bresenham(xStepperMotor, yStepperMotor, x, y, x_dir, y_dir);    
        } else { // y = lead
            bresenham(yStepperMotor, xStepperMotor, y, x, y_dir, x_dir);
        }
    }

};

```

---

# Construction
fuck you, find your own parts. I dont care about the nobody reading this to spend my time on this :D
# Code Documentation

Good luck figuring it out on your own. I have no idea either.

## Libraries used:
I have no clue. 
Just go check it lol.