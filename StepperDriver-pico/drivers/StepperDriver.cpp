#include "StepperDriver.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <cmath>

StepperDriver::StepperDriver(Stepper::stepper_pins pins_x, Stepper::stepper_pins pins_y)
        : xStepperMotor(pins_x),
          yStepperMotor(pins_y) {
    const int STEPS_P_ROT = 1000;
    const int ROD_PITCH_mm = 2;

    const int USE_SPROFILE_FROM_STEPS = 200;
    const int STEPS_P_1MM = STEPS_P_ROT / ROD_PITCH_mm;
    const double MM_p_STEP = (double)1 / STEPS_P_1MM;
};
void StepperDriver::move(int x, int y){
    if(x == 0 && y == 0){return;}
    // update stepper pos
    x_pos += x; 
    y_pos += y;

    bool x_dir = (x<0) ? true : false; // change if the direction is wrong
    bool y_dir = (y<0) ? true : false;

    // set both to positive
    x = abs(x); y = abs(y);

    if (x >= y){ // x = lead
        bresenham(xStepperMotor, yStepperMotor, x, y, x_dir, y_dir);    
    } else {
        bresenham(yStepperMotor, xStepperMotor, y, x, y_dir, x_dir);
    }
    return;
};

void StepperDriver::bresenham(Stepper leadStepper, Stepper followStepper, int lead, int follow, bool leadDir, bool followDir){
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
        if (diffFollowCycle != 0){
            leadStepper.step_firstHalf(leadDir);
            followStepper.step_firstHalf(followDir); // move the follow if needed
            sleep_us(motor_sleep_us);
            leadStepper.step_secondHalf();
            followStepper.step_secondHalf();
            sleep_us(motor_sleep_us);

        } else {
            leadStepper.step_firstHalf(leadDir);
            sleep_us(motor_sleep_us);
            leadStepper.step_secondHalf();
            sleep_us(motor_sleep_us);
        }
    }
    return;
}

void StepperDriver::pos_reset(){
    x_pos = y_pos = 0;
};

void StepperDriver::printPosToTermial(){
    printf("head pos: X: %.4fmm, Y: %.4fmm \n", (x_pos * MM_p_STEP), (y_pos * MM_p_STEP)); // round up to 4 digets -> r(10**4)/10**4
};