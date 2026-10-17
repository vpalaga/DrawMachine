#include "Led.h"
#include "pico/stdlib.h"
#include <cmath>

Led::Led(int const pin_init_){
    pin = pin_init_;
    
    gpio_init(pin);             // initialize the GPIO pin
    gpio_set_dir(pin, GPIO_OUT);// set it as output
}

void Led::toggleLed(){
    state = !state;

    gpio_put(pin, state);
}

void Led::setState(bool set_to){
    if (set_to != state){
        state = set_to;

        gpio_put(pin, state);
    }
}

void Led::setBrightness(int duration_ms, float br){
    // duration is in ms, cycle is in us
    int cycles = (duration_ms * 1000) / cycleDuration_us;

    float on_us = br * cycleDuration_us;
    float off_us = cycleDuration_us - on_us; 

    setState(false);
    
    for (int i = 0; i < cycles; i++){
        toggleLed();
        sleep_us(on_us);
        toggleLed();
        sleep_us(off_us);
    }
}