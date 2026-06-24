#ifndef STEPPERDRIVER_H
#define STEPPERDRIVER_H

#include "Stepper.h"

class StepperDriver {
public:
    int x_sleep_us = 100;
    int y_sleep_us = 100; 

    bool x_dir = true;
    bool y_dir = true;

    bool x_enabled = true;
    bool y_enabled = true;

    StepperDriver(int x_stp,int x_dir,int y_stp,int y_dir, int _minCycles, int _maxCycles, bool _autoCycle);
    int gcd(int a, int b);
    int calculate_match_cycles();
    void move_at_speed();
    void move(int motor, int delay);

    void simple_spin();

private:
    Stepper xStepperMotor;
    Stepper yStepperMotor;

    int minCycles;
    int maxCycles;

    bool autoCycle;

    bool x_fisrt_cycle = false;
    bool y_fisrt_cycle = false;

    // use to skip cycle calc if possible
    int x_last_sleep_us = -1;
    int y_last_sleep_us = -1;

    int last_cycle_calc = -1;


};

#endif