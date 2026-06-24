#include "SwitchButton.h"
#include "pico/stdlib.h"

SwitchButton::SwitchButton(int pin_init_, bool invert){ // GPIO pin of the swich
    pin = pin_init_;
    invertOnReturn = invert;

    gpio_init(pin);
    gpio_set_dir(pin, GPIO_IN);
    // set up the PINS thru internal resisitor to 50KΩ
    gpio_pull_up(pin); // enable internal pull-up
}

bool SwitchButton::getSwichState(){
    // false = open, true = closed -> stop movement
    // check wheter they are pulling any current
    
    if (!gpio_get(pin)) {   // LOW = pressed
        return !invertOnReturn;
    } else {
        return invertOnReturn;
    }
}