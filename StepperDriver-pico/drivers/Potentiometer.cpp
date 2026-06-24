#include "Potentiometer.h"
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include <stdio.h>
#include <cmath>


Potentiometer::Potentiometer(int pin, int adcInput, bool invert){
    adcPin = pin;
    adcChannel = adcInput;
    _invert = invert;
    // init the adc pin
    adc_gpio_init(pin);
};

float Potentiometer::get_value(){
    // return float between 0 and 1
    adc_select_input(adcChannel);
    int raw = adc_read();
    
    if (_invert){raw = 4095 - raw;}

    return raw / 4095.0f;
};

int Potentiometer::apply_between(int a, int b, bool expCurve){
    // expected: a<b
    int range = b-a;
    float value = get_value();
    
    if (expCurve){
        // use x**4 curve as exponential
        return round(range * pow(value, 2)) + a;
    } else {
        // with a=0 f(0)=1, but im too lazy to fix
        return round(pow(range, value)) + a;
    }
};