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

bool Head::calibrate(int maxSteps) {
    stepper.enable(true);

    bool calibrated = moveUntilEndstopState(false, Z_DOWN, maxSteps)
                   && moveUntilEndstopState(true, Z_UP, maxSteps);

    stepper.enable(false);
    if (calibrated) {
        penDownState = false;
    }
    return !calibrated;
}

bool Head::penUp(int steps) {
    if (!penDownState) {
        return true;
    }

    stepper.move(steps, stepSleepUs);
    penDownState = false;
    return false;
}

bool Head::penDown(int steps) {
    if (penDownState) {
        return true;
    }

    stepper.move(-steps, stepSleepUs);
    penDownState = true;
    return false;
}

bool Head::isPenDown() const {
    return penDownState;
}

void Head::setSpeed(int sleepUs) {
    stepSleepUs = sleepUs;
}
