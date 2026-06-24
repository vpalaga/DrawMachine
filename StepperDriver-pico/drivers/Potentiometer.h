#ifndef POTENTIOMETER_H
#define POTENTIOMETER_H

class Potentiometer {
public:
    Potentiometer(int pin, int adcInput, bool invert=false);
    float get_value();
    int apply_between(int a, int b, bool expCurve=false);
private:
    bool _invert;
    int adcPin;
    int adcChannel;
};
#endif