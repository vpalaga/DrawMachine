#include "StepperDriver.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <cmath>
#include <cstdlib>

StepperDriver::StepperDriver(Stepper::stepper_pins pins_x, Stepper::stepper_pins pins_y,
                             int xEndstopPin, int yEndstopPin)
        : xStepperMotor(pins_x),
          yStepperMotor(pins_y),
          xEndstop(xEndstopPin),
          yEndstop(yEndstopPin) {
}

void StepperDriver::move(int x, int y){
    if(x == 0 && y == 0){return;}
    // update stepper pos
    x_pos += x; 
    y_pos += y;

    bool x_dir = (x<0) ? false : true; // change if the direction is wrong
    bool y_dir = (y<0) ? false : true;

    // set both to positive
    x = std::abs(x); y = std::abs(y);

    if (x >= y){ // x = lead
        bresenham(xStepperMotor, yStepperMotor, x, y, x_dir, y_dir);    
    } else {
        bresenham(yStepperMotor, xStepperMotor, y, x, y_dir, x_dir);
    }
}

bool StepperDriver::calibrate() {
    enable(true);

    int steps = 0;
    while (!xEndstop.getSwichState() && !yEndstop.getSwichState()) {
        if (++steps > max_calibrate_steps_xy) {
            enable(false);
            return true;
        }
        move(-1, -1);
    }

    steps = 0;
    while (!xEndstop.getSwichState()) {
        if (++steps > max_calibrate_steps_xy) {
            enable(false);
            return true;
        }
        move(-1, 0);
    }

    steps = 0;
    while (!yEndstop.getSwichState()) {
        if (++steps > max_calibrate_steps_xy) {
            enable(false);
            return true;
        }
        move(0, -1);
    }

    pos_reset();
    return false;
}

void StepperDriver::bresenham(Stepper& leadStepper, Stepper& followStepper, int lead, int follow, bool leadDir, bool followDir){
    // how many steps of follow pro one step of lead
    float bresenhamStep = (float)follow / lead; // needs to be <= 1

    int followPos   = 0;
    int followCycle;
    int diffFollowCycle;
    
    for (int cycle = 1; cycle<lead+1; cycle++){ // cycle need to start at 1
        
        // calculate how many steps at current cycle position 
        followCycle = (int)std::round(cycle*bresenhamStep);
        
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
}

void StepperDriver::enable(bool setState){
    xStepperMotor.enable(setState);
    yStepperMotor.enable(setState);
}

void StepperDriver::pos_reset(){
    x_pos = y_pos = 0;
}

void StepperDriver::printPosToTermial(){
    printf("head pos: X: %.4fmm, Y: %.4fmm \n",
           (x_pos / STEPS_PER_MM), (y_pos / STEPS_PER_MM));
}

bool StepperDriver::xEndstopState(){
    return xEndstop.getSwichState();
}

bool StepperDriver::yEndstopState(){
    return yEndstop.getSwichState();
}