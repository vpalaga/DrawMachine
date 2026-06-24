#ifndef LED_H
#define LED_H

class Led {
public:
    bool state = false;

    Led(int const pin_init_);
    void toggleLed();
    void setState(bool set_to);
    void setBrightness(int duration_ms, float br);

private:
    int pin;
    int cycleDuration_us = 50;
};

#endif