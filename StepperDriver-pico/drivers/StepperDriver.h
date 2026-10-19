#ifndef STEPPERDRIVER_H
#define STEPPERDRIVER_H

#include "Stepper.h"
class StepperDriver {
public:
    int motor_sleep_us = 50;
    
    bool x_dir = false;
    bool y_dir = false;

    StepperDriver(Stepper::stepper_pins pins_x, Stepper::stepper_pins pins_y);
    void move(int x, int y);
    // steppers are taken by reference so the direction cache of the real motor is used
    void bresenham(Stepper& leadStepper, Stepper& followStepper, int lead, int follow, bool leadDir, bool followDir);
    void enable(bool setState);
    void pos_reset();
    void printPosToTermial();

    int x_pos = 0;
    int y_pos = 0;

private:
    Stepper xStepperMotor;
    Stepper yStepperMotor;

    int USE_SPROFILE_FROM_STEPS = 200;
    double MM_p_STEP = 0.002;
};

#endif