#include "Stepper.h"
#include "pico/stdlib.h"

Stepper::Stepper(int stepPin_init_, int dirPin_init_){
    stepPin = stepPin_init_;
    dirPin = dirPin_init_;
    
    // init the out pis for the stepper
    gpio_init(stepPin);
    gpio_set_dir(stepPin, GPIO_OUT);

    gpio_init(dirPin);
    gpio_set_dir(dirPin, GPIO_OUT);
};

void Stepper::step_firstHalf(bool dir){
    // make this as fast as possible...
    // change pin only when needed
    if (direction != dir) {
        gpio_put(dirPin, dir);
        direction = dir;
    }

    gpio_put(stepPin, 1);
};

void Stepper::step_secondHalf(){
    gpio_put(stepPin, 0);
};