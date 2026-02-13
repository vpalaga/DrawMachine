# Draw Machine by VPalaga 

The idea is to create a 2 axis (x, y) robot that can be controlled by the .FCODE protocol. Adding the Z   
axis shouldn't be very difficult, just raise the frame and move the print plane down. The FCODE is my    
own simplification of .gcode protocol.  

**The Goal: 100% working reliable x, y system.** 

>Partially based on Scrabble bot Code.
---

## .FCODE
>**FCODE Generation example in `FCODEgenerator/useExample.py`**  

``` python
from FCODEgenerator.main import FGenerator

gen = FGenerator("train_v1.dxf", acc=.1, vis_scale=10, text=False)
gen.gen_instructions()
gen.save()

```

Payload from Pi to Pico example:
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

> Current functions: (can be found under `FCODE generator.segmentFunctions.Instruction.instructions_parameters_len.keys()`

---
## Raspberry Pi
*Python on Raspberry Pi 4B*   
+ file reading
+ run `MotorControl`
+ send float x, y coordinates to Raspberry Pico 2W
+ control servo on the head (*depending on the current use*) or head in general
+ > maybe even web server host for FCODE upload or remote stearing



> To implement multifunctions, the Inscructions need to have be adjusted to the new argument length 
---
## Raspberry Pico  
Microcontroller running the main `c` loop, basicaly the PICO is just a dual simultanious stepper driver: 
+ recive functions
+ respond with error/confirmantion messages
+ drive the end swiches   
+ Send logic to x, y TMC 2209 Drivers

I am using **Raspberry Pi Pico VS Code extension** to write, compile and upload the program to my Pico.

---
### The idea for the c++ code running on the pico:
USB CDC Virtual Serial data exchange, to send `MOVE` coordinates to the pico.

> CDC Example
``` cpp
// Pico: client
while (true) {
        if (stdio_usb_connected()) {
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
# Raspebrry Pi: host

# replace with your Pico’s serial port name;
# on Linux it might be "/dev/ttyACM0" or similar
# on Windows something like "COM3"
SERIAL_PORT = "/dev/ttyACM0" #
BAUDRATE = 115200

# open the serial connection
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

time.sleep(2)    # short delay to let the port settle

# send a line to the Pico
ser.write(b"Hello from Python host!\r\n")
```


---

# Construction
| Part | Amount  | Function |  Notes |
| ---- | ------  | -------- | ----- |
| 2020 500 Aluminium Profile | 3 | the rails for x, y head/ train movement | 2 for y, 1 for x |
| 3030 250 Aluminium Profile | 4 | construction | |
| 3030 350 Aluminium Profile | 4 | construction | main cross construction |
| T8 500 Groove rod | 2 | movement|  |
||||||
| PLA fillament| ~2kg | print | not shure about the amount |
||||||
| TMC 2209 Stepper Driver | 2 | drive the steppers | one for each |
| End swich KW12 | 2 | endswiches to calibrate | use terminals 1, 2 (conduct when pressed) |
| Nema 17 Stepper | 2 | move in the x, y | 17HE08-1004S | 
||||||
| 4x13x5mm Beraring | lot | train, head, movement | |
| 8x22x7mm Beraring | 4 | rod end | for y motor needed one extra for the strart |
||||||
| M3 8mm hex bolt| ~150 | mate | not shure about the amount|
| M3 10mm hex bolt| ~10 | secure the top to the ALU bot | M3 12mm also possible |  
| M3 12mm hex bolt| ~30 | mate | not shure about the amount|
| M3 nut | ~80 | mate | not shure about the amount |

