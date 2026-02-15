#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/timer.h"
#include "hardware/clocks.h"
#include "algorithm"

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


// end swich pins
// deifne the GPIO ports of the draw swiches terminals
// both thru swich to GND (pin 33, one above)
const int X_SWICH_GPIO = 26; // pin 31
const int Y_SWICH_GPIO = 27; // pin 32

// define the TMC2209 pins 1
const int X_DIR_STEPPER_PIN = 20;
const int X_STP_STEPPER_PIN = 21;

// TMC 2
const int Y_DIR_STEPPER_PIN = 18;
const int Y_STP_STEPPER_PIN = 19;

// LEDs wire to GND (pin 23)
const int LED_1_PIN = 16;
const int LED_2_PIN = 17;

// CDC buffer max len
static const int BUF_MAX_LEN = 128;

//=============================================================

// stuff for CDC full string recive
char rx_buf[BUF_MAX_LEN];
int rx_pos = 0;

// state of recived message
bool recivedMessageState;

//=============================================================


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
            state = !state;

            gpio_put(pin, state);
        }

        void setState(bool set_to){
            state = set_to;

            gpio_put(pin, state);
        }
};

class Stepper{
    public:
        uint stepPin;
        uint dirPin;
        int us_delay;

        Stepper(uint stepPin_init_, uint dirPin_init_, int us_delay_init_){
            stepPin = stepPin_init_;
            dirPin = dirPin_init_;
            us_delay = us_delay_init_;
            
            // init the out pis for the stepper
            gpio_init(stepPin);
            gpio_set_dir(stepPin, GPIO_OUT);

            gpio_init(dirPin);
            gpio_set_dir(dirPin, GPIO_OUT);

        }

        void step(bool dir, int steps, int delay){
            us_delay = delay;

            gpio_put(dirPin, dir);

                for (int i = 0; i < steps; i++) {
                    gpio_put(stepPin, 1);
                    sleep_us(us_delay);

                    gpio_put(stepPin, 0);
                    sleep_us(us_delay);
                }
        }

};

// wait for connection
void waitForCDC(){
    while (!stdio_usb_connected()) {
        sleep_ms(100);
    }
}

bool process_received(const char *buf, int len) {
    // return false (0): the message is OK 
    // return true  (1): the message is unsable
    // handle complete message (null-terminated)
    //printf("Got: %s\n", buf);
    return false;
}

void confirm_recive(bool state){
    // false = all good
    // true error
    printf("%d\n", state); // dont forget to end message by '\n'
}

int main()
{
    if (true){ // for editor, can be hidden
    
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
    }

    //set up the x,y end swiches
    //Swich xSwich(X_SWICH_GPIO); // GPIo 26
    //Swich ySwich(Y_SWICH_GPIO); // GPIO 27
    
    // leds
    //LED redLed(13);
    //LED greenLed(14);

    //Steppers
    Stepper xStepper(X_STP_STEPPER_PIN, X_DIR_STEPPER_PIN, 1000);

    printf("USB CDC serial ready!\n");

    while (true) {
        // get full buffer
        while (true) {
            int c = getchar_timeout_us(0);
            if (c == PICO_ERROR_TIMEOUT) break;     // no more data
            if (rx_pos < BUF_MAX_LEN - 1) {
                rx_buf[rx_pos++] = (char)c;
            }
            // optional: detect end-of-line to process early, should allways be the case
            if (c == '\n' || c == '\r') {
                break;
            }
        }

        if (rx_pos > 0) {
            rx_buf[rx_pos] = '\0';    // null terminate
            
            // save the state, false=good, true=unusable
            recivedMessageState = process_received(rx_buf, rx_pos);
            // send out the state
            confirm_recive(recivedMessageState);
            
            // reset for next message
            rx_pos = 0;
        }

        sleep_ms(1); // bottle neck, ignore for now
    }
    
}
