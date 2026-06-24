#ifndef SWITCHBUTTON_H
#define SWITCHBUTTON_H

class SwitchButton {
public:
    SwitchButton(int pin_init_, bool invert = false);
    bool getSwichState();

private:
    int pin;
    bool invertOnReturn;
};

#endif