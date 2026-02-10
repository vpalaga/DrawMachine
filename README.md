# Draw Machine by VPalaga 

The idea is to create a 2d axis robot that can be controlled by the .FCODE protocol.  
The Goal: 100% working reliable x, y system. 

>Partially based on Scrabble bot Code.
---

## .FCODE
>**FCODE Generation example in `FCODEgen.master.py`**  
   
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
| WAIT |  1 |wait *x* seconds |
| CALIBRATE | 0 | calibrate the head (using the swiches at 0, 0) |
| *PENUP* | 0 | set the pen positon to be up |
| *PENDOWN* | 0 | set the pen position to be down|   

> Current functions: (can be found under `FCODEgen.segmentFunctions.Instruction.instructions_parameters_len.keys()`

---
## Raspberry Pi
*Python on Raspberry Pi 4B*   
+ File reading
+ move generation
+ send float x, y coordinates to Raspberry Pico 2W
+ control servo on the head (*depending on the current use*)
+ > maybe even web server host for FCODE upload or remote stearing



> To implement multifunctions, the Inscructions need to have be adjusted to the new argument length 
---
## Raspberry Pico  
Microcontroller running a `c` loop: 
+ recive functions
+ respond with error/confirmantion messages
+ control the end swiches   
+ Send logic to x, y TMC 2209 Drivers   
---

# Construction
| Part | Amount  | Function |  Notes |
| ---- | ------  | -------- | ----- |
| 2020 500 Aluminium Profile | 3 | the rails for x, y head/ train movement | 2 for y, 1 for x |
| 3030 250 Aluminium Profile | 4 | construction | |
| 3030 350 Aluminium Profile | 4 | construction | main cross construction |
| Nema 17 Stepper | 2 | move in the x, y | 17HE08-1004S | 
| End swich KW12 | 2 | endswiches to calibrate | use terminals 1, 2 (conduct when pressed) |
| T8 500 Groove rod | 2 | movement|  |
| TMC 2209 Stepper Driver | 2 | drive the steppers | one for each |
| 4x13x5mm Beraring | lot | train, head, movement | |
| 8x22x7mm Beraring | 4 | rod end | for y motor needed one extra for the strart |
| PLA fillament| ~2kg | print | not shure about the amount |
| M3 8mm hex bolt| ~150 | mate | not shure about the amount|
| M3 12mm hex bolt| ~30 | mate | not shure about the amount|
| M3 nut | ~80 | mate | not shure about the amount |
| PCA9685 | 1 | servo control | conn to  RSB pi |
