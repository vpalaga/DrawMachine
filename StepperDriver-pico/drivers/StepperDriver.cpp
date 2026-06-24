#include "StepperDriver.h"
#include "pico/stdlib.h"
#include <cmath>

StepperDriver::StepperDriver(int x_stp,int x_dir,int y_stp,int y_dir, int _minCycles, int _maxCycles, bool _autoCycle)

    : xStepperMotor(x_stp, x_dir),
      yStepperMotor(y_stp, y_dir) {
    
    minCycles = _minCycles;
    maxCycles = _maxCycles;
    autoCycle = _autoCycle;

};

void StepperDriver::move_at_speed(){
    // if cycles < 0: use auto compute for min_c = |cycles|
    int cycles;
    // auto cycle calc
    if (autoCycle){
        if (x_sleep_us == x_last_sleep_us && y_sleep_us == y_last_sleep_us) {
            // same as last cycle -> use last cycle val
            cycles = last_cycle_calc;
        } else {
            cycles = calculate_match_cycles();
            // update data for next time
            x_last_sleep_us = x_sleep_us;
            y_last_sleep_us = y_sleep_us;
            last_cycle_calc = cycles;
        }
    }

    int xMotorMultiplier = 0;
    int yMotorMultiplier = 0;
    
    int time = 0;
    int cycle = 0;

    int xNextTimeStamp;
    int yNextTimeStamp;

    // 0: x, 1: y, 2:xy
    // first cylce 
    move(2, 0);
    
    while (cycle < cycles){
        xNextTimeStamp = (xMotorMultiplier + 1) * x_sleep_us;
        yNextTimeStamp = (yMotorMultiplier + 1) * y_sleep_us;
    
        // case 1: they meet
        if(xNextTimeStamp == yNextTimeStamp){
            // cycle both motors at delay 
            move(2, xNextTimeStamp - time);
            
            // reset to 0 ? keep it to small numbers
            int xMotorMultiplier = 0;
            int yMotorMultiplier = 0;
            int time = 0;
            
        } else if (xNextTimeStamp < yNextTimeStamp){
            // x cycle 
            move(0, xNextTimeStamp - time);

            time = xNextTimeStamp;
            xMotorMultiplier ++;
        } else {
            // y cycle 
            move(1, yNextTimeStamp - time);

            time = yNextTimeStamp;
            yMotorMultiplier ++; 
        }
        cycle++;
    }
};

void StepperDriver::move(int motor, int delay){
    // sleep the delay
    sleep_us(delay);

    // if motor = 2 run both
    if (motor == 0 || motor == 2){
        if (x_fisrt_cycle) {
            xStepperMotor.step_firstHalf(x_dir);
            x_fisrt_cycle = false;
        } else {
            xStepperMotor.step_secondHalf();
            x_fisrt_cycle = true;
        }
    }

    if (motor == 1 || motor == 2){
        if (y_fisrt_cycle) {
            yStepperMotor.step_firstHalf(y_dir);
            y_fisrt_cycle = false;
        } else {
            yStepperMotor.step_secondHalf();
            y_fisrt_cycle = true;
        }
    }
};

int StepperDriver::gcd(int a, int b){
    while (b != 0) {
        const int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
};

int StepperDriver::calculate_match_cycles(){
    // calculate cycles so that the motor steps will match 
    // and should prevent unwanted motor behaviur
    /*
    ?? bug rep: maybe for some wired us_sleep times,
    the resuilt is large and that maight be causing the long cycles

    ?? fix:
    add a max cycle lenght and than 
    
    */ 
    int a = x_sleep_us; int b = y_sleep_us;

    const int g = gcd(a, b);
    int result = (a / g) * b;
    
    // make shure both motors have even nums of cycles (* 2)
    // theoreticly it doesnt matter, bc i keep the motor state anyway
    // they shift next method-call anyway...

    //if (a & 1 || b & 1) {
    //    result <<= 1;
    //}

    // make the result somme reasonable size
    if (result<minCycles){
        // maight fuck it up timing-wise
        int scaler = minCycles / result;
        return result * (scaler + 1); 
    } else if (result > maxCycles){
        return maxCycles;
    }

    return result;
};

void StepperDriver::simple_spin(){
    if (x_enabled && y_enabled){return;} // false call

    const int cycles = minCycles;

    // use move() to keep track of all motors
    if (x_enabled){
        for (int i; i<cycles; i++){
            move(0, x_sleep_us);
        }
    } else {
        for (int i; i<cycles; i++){
            move(1, y_sleep_us);
        }
    }
};