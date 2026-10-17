#include "Stepper.h"
#include "pico/stdlib.h"
#include <cstdlib>

Stepper::Stepper(stepper_pins pins_init){
    pins = pins_init;

    // init the out pis for the stepper
    gpio_init(pins.stepPin);
    gpio_set_dir(pins.stepPin, GPIO_OUT);

    gpio_init(pins.dirPin);
    gpio_set_dir(pins.dirPin, GPIO_OUT);
    gpio_put(pins.dirPin, 0);

    gpio_init(pins.enPin);
    gpio_set_dir(pins.enPin, GPIO_OUT);
    gpio_put(pins.enPin, 1); // start disabled
}

void Stepper::step_firstHalf(bool dir){
    // make this as fast as possible...
    // change pin only when needed
    if (direction != dir) {
        gpio_put(pins.dirPin, dir);
        direction = dir;
    }

    gpio_put(pins.stepPin, 1);
}

void Stepper::step_secondHalf(){
    gpio_put(pins.stepPin, 0);
}

void Stepper::enable(bool setState){ // true: enabled, false: disabled
    enabled = setState;
    gpio_put(pins.enPin, setState ? 0 : 1);
}

void Stepper::stepOnce(bool dir, int sleep){
    step_firstHalf(dir);
    sleep_us(sleep);
    step_secondHalf();
    sleep_us(sleep);
}

void Stepper::move(int steps, int sleep){
    bool dir = steps < 0;          // steps >= 0 -> dir pin 0, steps < 0 -> dir pin 1
    int count = std::abs(steps);

    // disable the motor after to keep it from overheating, but might shift the holder down.
    enable(true);
    for (int s = 0; s < count; s++){
        stepOnce(dir, sleep);
    }
    enable(false);
}