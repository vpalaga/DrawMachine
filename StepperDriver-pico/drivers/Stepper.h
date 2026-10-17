#ifndef STEPPER_H
#define STEPPER_H

#include <cstdint>

class Stepper {
public:
    struct stepper_pins{
        std::uint8_t stepPin;
        std::uint8_t dirPin;
        std::uint8_t enPin;
    };


    Stepper(stepper_pins pins);
    void step_firstHalf(bool dir);
    void step_secondHalf();
    void enable(bool setState);

    // one full step pulse (does NOT touch the enable pin)
    void stepOnce(bool dir, int sleep);
    // move |steps| steps, steps < 0 = other direction. Enables, then disables the motor.
    void move(int steps, int sleep);

    int us_delay = 0;
    bool enabled = false;

private:
    stepper_pins pins;
    bool direction = false;
};

#endif