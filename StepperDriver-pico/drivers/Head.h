#ifndef HEAD_H
#define HEAD_H

#include "Stepper.h"
#include "SwitchButton.h"

class Head {
public:
    Head(Stepper::stepper_pins stepperPins, int endstopPin);

    bool calibrate(int maxSteps);
    bool penUp(int steps);
    bool penDown(int steps);
    bool isPenDown() const;
    void setSpeed(int sleepUs);

private:
    static constexpr bool Z_UP = false;
    static constexpr bool Z_DOWN = true;

    bool moveUntilEndstopState(bool targetState, bool direction, int maxSteps);

    Stepper stepper;
    SwitchButton endstop;
    int stepSleepUs = 100;
    bool penDownState = false;
};

#endif