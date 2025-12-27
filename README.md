# Draw Machine (bot) by VPalaga 

---

>The idea is to create a 2d axis robot that can be controlled by the .FCODE protocol.
The Goal: 100½ working resalable x, y system. 

Based on Scrabble bot Code.

FCODE Generation example in `FCODEgen.master.py`


Raspberry Pi 4B: File reading, move generation send raw int x, y coordinates to:
/ servo control 
> maybe even web server host for FCODE upload or remote stearing

Raspberry Pico: Send raw binary inputs to X; Y -> TMC Drivers 



- The nozzle is based on 2 500mm 20x20mm aluminium extrusions.

- Designed for 2 Nema 17 Steppers [basic 23mm]
- 2 buttons at each 0 position for calibration. (feed into Raspberry Pi)
- 2 500mm 8mm grooved rods with pitch 2mm for x, y movement

