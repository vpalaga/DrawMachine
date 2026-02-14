#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/timer.h"
#include "hardware/clocks.h"

// I2C defines
// This example will use I2C0 on GPIO8 (SDA) and GPIO9 (SCL) running at 400KHz.
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define I2C_PORT i2c0
#define I2C_SDA 8
#define I2C_SCL 9

// end swich pins
// deifne the GPIO ports of the draw swiches terminals
// both thru swich to GND (pin 33, one above)
#define X_SWICH_GPIO 26 // pin 31
#define Y_SWICH_GPIO 27 // pin 32

int64_t alarm_callback(alarm_id_t id, void *user_data) {
    // Put your timeout handler code in here
    return 0;
}

// toggle function true -> false; false -> true
bool toggleValue(bool input) { return !input; }

class Swich{
    public:
        // GPIO Pin
        uint pin;
        Swich(uint pin_init_){ // GPIO pin of the swich
            pin = pin_init_;

            gpio_init(pin);
            gpio_set_dir(pin, GPIO_IN);
            // set up the PINS thru internal resisitor to 50KΩ
            gpio_pull_up(pin);   // enable internal pull-up
        }

        bool getSwichState(){
            // false = open, true = closed -> stop movement
            // check wheter they are pulling any current
            
            if (!gpio_get(pin)) {   // LOW = pressed
                printf("Switch at %d pressed \n", pin);
                return true;

            } else {
                printf("Switch at %d released\n", pin);
                return false;
            }
        }

};

class LED{
    public:
        uint pin;
        bool state = false;

        LED(uint pin_init_){
            pin = pin_init_;
            
            gpio_init(pin);             // initialize the GPIO pin
            gpio_set_dir(pin, GPIO_OUT);// set it as output
        }

        void toggleLed(){
            state = toggleValue(state);

            gpio_put(pin, state);
        }

        void setState(bool set_to){
            state = set_to;

            gpio_put(pin, state);
        }
};

int main()
{
    stdio_init_all();

    // I2C Initialisation. Using it at 400Khz.
    i2c_init(I2C_PORT, 400*1000);
    
    gpio_set_function(I2C_SDA, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA);
    gpio_pull_up(I2C_SCL);
    // For more examples of I2C use see https://github.com/raspberrypi/pico-examples/tree/master/i2c

    // Timer example code - This example fires off the callback after 2000ms
    add_alarm_in_ms(2000, alarm_callback, NULL, false);
    // For more examples of timer use see https://github.com/raspberrypi/pico-examples/tree/master/timer

    printf("System Clock Frequency is %d Hz\n", clock_get_hz(clk_sys));
    printf("USB Clock Frequency is %d Hz\n", clock_get_hz(clk_usb));
    // For more examples of clocks use see https://github.com/raspberrypi/pico-examples/tree/master/clocks

    //set up the x,y end swiches
    Swich xSwich(X_SWICH_GPIO); // GPIo 26
    Swich ySwich(Y_SWICH_GPIO); // GPIO 27
    
    // leds
    LED redLed(13);
    LED greenLed(14);

    while (true) {
        bool state = ySwich.getSwichState();
        
        redLed.setState(state);
        greenLed.setState(!state);

        sleep_ms(50);

    }
}
