#ifndef STEPPERDRIVER_H
#define STEPPERDRIVER_H

#include "Stepper.h"
#include "SwitchButton.h"

class StepperDriver {
public:
    int motor_sleep_us = 50;
    
    bool x_dir = false;
    bool y_dir = false;

    StepperDriver(Stepper::stepper_pins pins_x, Stepper::stepper_pins pins_y,
                  int xEndstopPin, int yEndstopPin);
    void move(int x, int y);
    bool calibrate();
    // steppers are taken by reference so the direction cache of the real motor is used
    void bresenham(Stepper& leadStepper, Stepper& followStepper, int lead, int follow, bool leadDir, bool followDir);
    void enable(bool setState);
    void pos_reset();
    void printPosToTermial();
    bool xEndstopState();
    bool yEndstopState();

    int x_pos = 0;
    int y_pos = 0;

private:
    static constexpr int max_calibrate_steps_xy = 400000;
    static constexpr double STEPS_PER_MM = 800.0;

    Stepper xStepperMotor;
    Stepper yStepperMotor;
    SwitchButton xEndstop;
    SwitchButton yEndstop;

    int USE_SPROFILE_FROM_STEPS = 200;
};

#endif