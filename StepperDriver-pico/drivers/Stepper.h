#ifndef STEPPER_H
#define STEPPER_H

class Stepper {
public:
    int us_delay;

    Stepper(int stepPin_init_, int dirPin_init_);
    void step_firstHalf(bool dir);
    void step_secondHalf();
private:
    int stepPin;
    int dirPin;
    bool direction;
};

#endif