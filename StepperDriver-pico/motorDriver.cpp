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

int64_t alarm_callback(alarm_id_t id, void *user_data) {
    // Put your timeout handler code in here
    return 0;
}

// deifne the GPIO ports of the draw swiches terminals
const uint X_SWICH_GPIO;
const uint Y_SWICH_GPIO;

class Swich{
    public:
        uint pin;
        Swich(uint pin_init_){ // GPIO pin of the swich
            pin = pin_init_;
        }

    bool getSwichState(){
        // false = open, true = closed -> stop movement
        // set up the PINS thru internal resisitor to 50KOhms
        // check wheter they are pulling any current
        
    }

};


int main()
{
    stdio_init_all();

    // I2C Initialisation. Using it at 400Khz.
    i2c_init(I2C_PORT, 400*1000);
    
    sleep_ms(5000);

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
    Swich xSwich(X_SWICH_GPIO);
    Swich ySwich(Y_SWICH_GPIO);

    while (true) {
        sleep_ms(1000);
        printf("Hello, world!\n");
    }
}
// time to sleep fucker :D