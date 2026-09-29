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

    void move(int steps, int sleep);

    int us_delay;
    bool enabled = false;

private:
    stepper_pins pins;
    bool direction = false;
};

#endif