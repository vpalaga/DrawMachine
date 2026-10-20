#include "Head.h"
#include "pico/stdlib.h"

Head::Head(Stepper::stepper_pins stepperPins, int endstopPin)
        : stepper(stepperPins),
          endstop(endstopPin) {
}

bool Head::moveUntilEndstopState(bool targetState, bool direction, int maxSteps) {
    int steps = 0;
    while (true) {
        while (endstop.getSwichState() != targetState) {
            if (steps >= maxSteps) {
                return false;
            }

            stepper.stepOnce(direction, stepSleepUs);
            ++steps;
        }

        sleep_ms(5);
        if (endstop.getSwichState() == targetState) {
            return true;
        }
    }
}

bool Head::calibrate() {
    stepper.enable(true);
    sleep_ms(10);
    bool calibrated = moveUntilEndstopState(false, Z_DOWN, max_calibrate_steps_z)
                   && moveUntilEndstopState(true, Z_UP, max_calibrate_steps_z);

    stepper.enable(false);
    if (calibrated) {
        penDownState = false;
    }
    return !calibrated;
}

bool Head::penUp() {
    const int fixedUpSteps = move_steps_up * fixed_up_percent / 100;
    const int switchSeekSteps = move_steps_up * (100 - fixed_up_percent + switch_seek_extra_percent) / 100;

    sleep_ms(500);

    stepper.enable(true);
    for (int step = 0; step < fixedUpSteps; ++step) {
        stepper.stepOnce(Z_UP, stepSleepUs);
    }

    bool reachedEndstop = moveUntilEndstopState(true, Z_UP, switchSeekSteps);
    stepper.enable(false);

    if (reachedEndstop) {
        penDownState = false;
    }
    return !reachedEndstop;
}

bool Head::penDown() {
    if (penDownState) {
        return true;
    }

    stepper.move(-move_steps_up, stepSleepUs);
    penDownState = true;
    return false;
}

bool Head::isPenDown() const {
    return penDownState;
}

void Head::setSpeed(int sleepUs) {
    stepSleepUs = sleepUs;
}

bool Head::setMoveStepsUp(int steps) {
    if (steps <= 0 || steps > max_calibrate_steps_z) {
        return true;
    }

    move_steps_up = steps;
    return false;
}
