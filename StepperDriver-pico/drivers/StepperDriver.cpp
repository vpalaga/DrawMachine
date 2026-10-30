#include "StepperDriver.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <limits>

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
    const uint64_t pulseWidthUs = static_cast<uint64_t>(motor_sleep_us);
    const uint64_t leadPeriodUs = pulseWidthUs * 2;
    // Both axes span the same move duration; follow pulses are evenly timed within it.
    const uint64_t moveDurationUs = static_cast<uint64_t>(lead) * leadPeriodUs;
    const absolute_time_t startTime = get_absolute_time();

    int leadSteps = 0;
    int followSteps = 0;
    bool leadPulseHigh = false;
    bool followPulseHigh = false;
    uint64_t leadFallUs = 0;
    uint64_t followFallUs = 0;

    while (leadSteps < lead || followSteps < follow || leadPulseHigh || followPulseHigh) {
        uint64_t nextEventUs = std::numeric_limits<uint64_t>::max();

        if (leadSteps < lead) {
            nextEventUs = std::min(nextEventUs, static_cast<uint64_t>(leadSteps) * leadPeriodUs);
        }
        if (followSteps < follow) {
            const uint64_t followRiseUs =
                    static_cast<uint64_t>(followSteps) * moveDurationUs / static_cast<uint64_t>(follow);
            nextEventUs = std::min(nextEventUs, followRiseUs);
        }
        if (leadPulseHigh) {
            nextEventUs = std::min(nextEventUs, leadFallUs);
        }
        if (followPulseHigh) {
            nextEventUs = std::min(nextEventUs, followFallUs);
        }

        busy_wait_until(delayed_by_us(startTime, nextEventUs));

        if (leadPulseHigh && leadFallUs == nextEventUs) {
            leadStepper.step_secondHalf();
            leadPulseHigh = false;
        }
        if (followPulseHigh && followFallUs == nextEventUs) {
            followStepper.step_secondHalf();
            followPulseHigh = false;
        }

        if (leadSteps < lead
                && static_cast<uint64_t>(leadSteps) * leadPeriodUs == nextEventUs) {
            leadStepper.step_firstHalf(leadDir);
            ++leadSteps;
            leadPulseHigh = true;
            leadFallUs = nextEventUs + pulseWidthUs;
        }
        if (followSteps < follow
                && static_cast<uint64_t>(followSteps) * moveDurationUs
                   / static_cast<uint64_t>(follow) == nextEventUs) {
            followStepper.step_firstHalf(followDir);
            ++followSteps;
            followPulseHigh = true;
            const uint64_t nextFollowRiseUs = followSteps < follow
                    ? static_cast<uint64_t>(followSteps) * moveDurationUs / static_cast<uint64_t>(follow)
                    : moveDurationUs;
            followFallUs = nextEventUs + (nextFollowRiseUs - nextEventUs) / 2;
        }
    }

    busy_wait_until(delayed_by_us(startTime, moveDurationUs));
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