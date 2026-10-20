#ifndef HEAD_H
#define HEAD_H

#include "Stepper.h"
#include "SwitchButton.h"

class Head {
public:
    Head(Stepper::stepper_pins stepperPins, int endstopPin);

    bool calibrate(int maxSteps);
    bool penUp();
    bool penDown();
    bool isPenDown() const;
    void setSpeed(int sleepUs);
    bool setMoveStepsUp(int steps);
    SwitchButton endstop;

private:
    static constexpr bool Z_UP = false;
    static constexpr bool Z_DOWN = true;
    int move_steps_up = 6500;
    static constexpr int fixed_up_percent = 95;
    static constexpr int switch_seek_extra_percent = 20;

    bool moveUntilEndstopState(bool targetState, bool direction, int maxSteps);

    Stepper stepper;
    int stepSleepUs = 100;
    bool penDownState = false;
};

#endif