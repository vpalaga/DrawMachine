# Draw Machine by VPalaga 

The idea is to make a plotter.

 The FCODE is my own simplification of .gcode protocol. I might implement the .gcode later for the sake of my own sanity, but for now I am working with my own fuck creation - FCODE.

look at use_examples they explane it better


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
ClB
MOV 45.478 3.671
PUP
MOV 67.092 89.082
PDN 
```
| Function  | Arguments | Description                        |
|-----------|-----------|------------------------------------|
| MOV       | 2         | move the head to the x, y position | 
| WAT       | 1         | wait *x* seconds                   |
| CLB       | 0         | calibrate x and y                  |
| HCB       | 0         | calibrate z                        |
| PUP       | 0         | set the pen up                     |
| PDN       | 0         | set the pen down                   |   
| SCM       | 1         | set console mode                   |   

> Current functions can be found under `FCODEgenerator.segmentFunctions.Instruction.instructions_parameters_len.keys()`

## Pico ## 
 - with cdc protocol receives text instructions 

 - serves as the computer to steer x, y, z steppers

 - has a line algorithm for xy MOV instructions
 - can calibrate the positions

---
### The idea for the c++ code running on the pico:
USB CDC Virtual Serial data exchange, to send `MOVE` coordinates to the pico.
