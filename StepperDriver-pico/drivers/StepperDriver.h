#ifndef STEPPERDRIVER_H
#define STEPPERDRIVER_H

#include "Stepper.h"
class StepperDriver {
public:
    int motor_sleep_us = 100;

    bool x_dir = true;
    bool y_dir = true;

    bool x_enabled = true;
    bool y_enabled = true;

    StepperDriver(int x_stp,int x_dir,int y_stp,int y_dir);
    void move(int x, int y);
    void bresenham(Stepper leadStepper, Stepper followStepper, int lead, int follow, bool leadDir, bool followDir);

    void pos_reset();
    void printPosToTermial();

private:
    Stepper xStepperMotor;
    Stepper yStepperMotor;

    int USE_SPROFILE_FROM_STEPS;
    double MM_p_STEP;
    
    int x_pos = 0;
    int y_pos = 0;
};

#endif