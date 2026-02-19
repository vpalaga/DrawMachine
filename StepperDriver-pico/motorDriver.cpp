#include <stdio.h>
#include <string>
#include <vector>
#include <sstream>
#include <map>
#include <math.h>
#include <cstdint>

#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/timer.h"
#include "hardware/clocks.h"
#include "hardware/i2c.h"

#include "algorithm"

using namespace std;


int64_t alarm_callback(alarm_id_t id, void *user_data) {
    // Put your timeout handler code in here
    return 0;
}


// end swich pins
// deifne the GPIO ports of the draw swiches terminals
// both thru swich to GND (pin 33, one above)
const int X_SWICH_GPIO = 26; // pin 31
const int Y_SWICH_GPIO = 27; // pin 32

// display
const int DISPLAY_CLK = 14;
const int DISPLAY_DIN = 15;

// define the TMC2209 pins 1
const int X_DIR_STEPPER_PIN = 20;
const int X_STP_STEPPER_PIN = 21;
// TMC 2
const int Y_DIR_STEPPER_PIN = 18;
const int Y_STP_STEPPER_PIN = 19;

// LEDs wire to GND (pin 23)
const int LED_INSTRUCTION_PIN = 17;
const int LED_SYSTEM = 25;
const int LED_2_PIN = 16; // no use now

// PCA9685 I2C0 and SDA, change maybe to consts later
// I2C defines
// This example will use I2C0 on GPIO8 (SDA) and GPIO9 (SCL) running at 400KHz.
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define I2C_PORT i2c0
#define I2C_SDA 8
#define I2C_SCL 9
#define PCA9685_ADDR 0x40

#define MODE1 0x00
#define PRESCALE 0xFE
#define LED0_ON_L 0x06

// CDC buffer max len, removed static date: 16.2.26
const int BUF_MAX_LEN = 128;

// instruction type vs arguments
const map<string, int> INSTRUCTION_SIZES = {
    {"MOV", 2},
    {"CLB", 0},
    {"WAT", 1},
    {"PUP", 0},
    {"PDN", 0}
};
//=============================================================

class PCA9685{
public:
    PCA9685(){
        // init the pins
        // I2C Initialisation. Using it at 400Khz.

        i2c_init(I2C_PORT, 400*1000);

        gpio_set_function(I2C_SDA, GPIO_FUNC_I2C);
        gpio_set_function(I2C_SCL, GPIO_FUNC_I2C);
        gpio_pull_up(I2C_SDA);
        gpio_pull_up(I2C_SCL);

        // For more examples of I2C use see https://github.com/raspberrypi/pico-examples/tree/master/i2c

        pca9685_init();
    }

    void pca9685_write(uint8_t reg, uint8_t value) {
        uint8_t buf[2] = {reg, value};
        i2c_write_blocking(I2C_PORT, PCA9685_ADDR, buf, 2, false);
    }

    void pca9685_init() {
        // Reset
        pca9685_write(MODE1, 0x00);
        sleep_ms(10);

        // Set PWM frequency to 50Hz
        float prescaleval = 25000000.0;
        prescaleval /= 4096.0;
        prescaleval /= 50.0;
        prescaleval -= 1.0;

        uint8_t prescale = (uint8_t)(prescaleval + 0.5);

        pca9685_write(MODE1, 0x10);        // Sleep
        pca9685_write(PRESCALE, prescale);
        pca9685_write(MODE1, 0x00);
        sleep_ms(5);
        pca9685_write(MODE1, 0xA1);        // Auto-increment
    }

    void set_pwm(uint8_t channel, uint16_t on, uint16_t off) {
        uint8_t reg = LED0_ON_L + 4 * channel;

        uint8_t buf[5]; // Some compilers treat this as narrowing from int to uint8_t.
        buf[0] = reg;
        buf[1] = (uint8_t)(on & 0xFF);
        buf[2] = (uint8_t)(on >> 8);
        buf[3] = (uint8_t)(off & 0xFF);
        buf[4] = (uint8_t)(off >> 8);
        
        i2c_write_blocking(I2C_PORT, PCA9685_ADDR, buf, 5, false);
    }

    void set_servo_angle(uint8_t channel, float angle) {
        float pulse_min = 205;  // ~1ms
        float pulse_max = 410;  // ~2ms

        float pulse = pulse_min + (angle / 180.0f) * (pulse_max - pulse_min);
        set_pwm(channel, 0, (uint16_t)pulse);
    }

};

class HW069{
    public:
        int8_t CLK;
        int8_t DIO;

        HW069(int CLK_init_,int DIO_init_){
            CLK = CLK_init_;
            DIO = DIO_init_;
            
            // Initialize GPIO pins used for the TM1637 interface
            gpio_init(CLK);
            gpio_init(DIO);
            gpio_set_dir(CLK, GPIO_OUT);
            gpio_set_dir(DIO, GPIO_OUT);
            // Idle high
            gpio_put(CLK, 1);
            gpio_put(DIO, 1);
        }

        uint8_t int_to_segment(int i){
            switch (i){
            case 0: return 0x3f; // 0
            case 1: return 0x06; // 1
            case 2: return 0x5b; // 2
            case 3: return 0x4f; // 3
            case 4: return 0x66; // 4
            case 5: return 0x6d; // 5
            case 6: return 0x7d; // 6
            case 7: return 0x07; // 7
            case 8: return 0x7f; // 8
            case 9: return 0x6f; // 9
            default: return 0x00;
            }
        }

        uint8_t char_to_segment(char c) {
            switch (c) {
            case '0': return 0x3F;
            case '1': return 0x06;
            case '2': return 0x5B;
            case '3': return 0x4F;
            case '4': return 0x66;
            case '5': return 0x6D;
            case '6': return 0x7D;
            case '7': return 0x07;
            case '8': return 0x7F;
            case '9': return 0x6F;
            case 'A': case 'a': return 0x77; // A
            case 'B': case 'b': return 0x7C; // b (lowercase-style)
            case 'C': case 'c': return 0x39; // C
            case 'D': case 'd': return 0x5E; // d (lowercase-style)
            case 'E': case 'e': return 0x79; // E
            case 'F': case 'f': return 0x71; // F
            case 'G': case 'g': return 0x6F; // G=9 
            case 'H': case 'h': return 0x76; // H
            case 'I': case 'i': return 0x06; // I=1
            case 'J': case 'j': return 0x1E; // J
            case 'L': case 'l': return 0x38; // L
            case 'P': case 'p': return 0x73; // P
            case 'U': case 'u': return 0x3E; // U
            case 'Y': case 'y': return 0x6E; // Y
            case 'V': case 'v': return 0x1c;

            case 'O': return 0x3F; // O=0
            case 'o': return 0x5c;

            case 'T': case 't': return 0x07; // t own
            case '-': return 0x40; // minus (g)
            case ' ': return 0x00; // blank
            case '_': return 0x08;
            case '"': return 0x22;
            default: return 0x00; // unknown -> blank
            }
        }

        void tm_delay() {
            sleep_us(5);
        }

        void tm_start() {
            gpio_set_dir(DIO, GPIO_OUT);
            gpio_put(DIO, 1);
            gpio_put(CLK, 1);
            tm_delay();
            gpio_put(DIO, 0);
        }

        void tm_stop() {
            gpio_put(CLK, 0);
            tm_delay();
            gpio_put(DIO, 0);
            tm_delay();
            gpio_put(CLK, 1);
            tm_delay();
            gpio_put(DIO, 1);
        }

        void tm_write(uint8_t data) {
            for (int i = 0; i < 8; i++) {
                gpio_put(CLK, 0);
                gpio_put(DIO, data & 0x01);
                tm_delay();
                gpio_put(CLK, 1);
                tm_delay();
                data >>= 1;
            }

            // ACK
            gpio_put(CLK, 0);
            gpio_set_dir(DIO, GPIO_IN);
            tm_delay();
            gpio_put(CLK, 1);
            tm_delay();
            gpio_set_dir(DIO, GPIO_OUT);
        }

        void display_number(int num) {
            uint8_t digits[4] = {
            int_to_segment((num / 1000) % 10),
            int_to_segment((num / 100) % 10),
            int_to_segment((num / 10) % 10),
            int_to_segment(num % 10)
            };

            tm_start();
            tm_write(0x40); // auto increment
            tm_stop();

            tm_start();

            tm_write(0xC0); // start at digit 0
            for (int i = 0; i < 4; i++)
            tm_write(digits[i]);
            tm_stop();

            tm_start();
            tm_write(0x8A); // display ON, brightness level 2
            tm_stop();
        }

        void display_text(const char *s) {
            uint8_t segs[4] = {0,0,0,0};
            // simple left align, show first 4 chars
            for (int i = 0; i < 4 && s[i]; ++i) segs[i] = char_to_segment(s[i]);
            
            tm_start();
            tm_write(0x40); // auto increment
            tm_stop();

            tm_start();
            tm_write(0xC0); // start at digit 0
            for (int i = 0; i < 4; ++i) tm_write(segs[i]);
            tm_stop();

            tm_start();
            tm_write(0x8A); // display ON, brightness level 2
            tm_stop();

        }
};

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
                return true;
            } else {
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

class StepperDriver{
public:

    Stepper xStepperMotor;
    Stepper yStepperMotor;

    StepperDriver()
        : xStepperMotor(X_STP_STEPPER_PIN, X_DIR_STEPPER_PIN, 100),
          yStepperMotor(Y_STP_STEPPER_PIN, Y_DIR_STEPPER_PIN, 100) {
    }
    void bresenham(Stepper leadStepper, Stepper followStepper, int lead, int follow, bool leadDir, bool followDir){
        // how many steps of follow pro one step of lead
        float bresenhamStep = (float)follow / lead; // needs to be <0 

        int followPos   = 0;
        int followCycle;
        int diffFollowCycle;

        for (int cycle = 1; cycle<lead+1; cycle++){ // cycle need to start at 1
            
            // calculate how many steps at current cycle position 
            followCycle = round(cycle*bresenhamStep);
            
            // check how many are needed for this cycle
            diffFollowCycle = followCycle - followPos;

            // update the followPos to current follow position
            followPos += diffFollowCycle;

            //move the steppers accordingly
            leadStepper.step(leadDir,1,100);
            followStepper.step(followDir,diffFollowCycle,100); // move the follow if needed
        }
    }

    void move(int x, int y){

        bool x_dir = (x<0) ? false : true; // change if the direction is wrong
        bool y_dir = (y<0) ? false : true;

        // set both to positive
        x = abs(x); y = abs(y);

        if (x >= y){ // x = lead
            bresenham(xStepperMotor, yStepperMotor, x, y, x_dir, y_dir);    
        } else {
            bresenham(yStepperMotor, xStepperMotor, y, x, y_dir, x_dir);
        }
    }
};

// display object
HW069 display(DISPLAY_CLK, DISPLAY_DIN);

// end swiches, use with calibrate
Swich xSwich(X_SWICH_GPIO); // GPIo 26
Swich ySwich(Y_SWICH_GPIO); // GPIO 27

// instruction led, when doing instruction than, on
LED instructionLed(LED_INSTRUCTION_PIN);

// driver
StepperDriver stepper_driver;

// servoDriver
PCA9685 servoDriver;   

class Instructions{
public:
    static bool wait(float seconds){
        instructionLed.setState(true);
        display.display_text("WAIT");

        sleep_ms(seconds*1000); // make into seconds

        display.display_text("----");
        instructionLed.setState(false);
        return false;
    }

    static bool move(int x, int y){
        instructionLed.setState(true);
        display.display_text("MOVE");

        stepper_driver.move(x, y);

        display.display_text("----");
        instructionLed.setState(false);
        return false; // move 
    }

    static bool calibrate(){
        instructionLed.setState(true);
        display.display_text("CALB");

        while (!xSwich.getSwichState()){ // dosnt conduct
            // i dont think a sleep is needed here, since 900 steps = 1mm move, so should be more than enough time to stop
            stepper_driver.move(-1, 0); // move one step x back (-)
        }

        display.display_text("----");
        instructionLed.setState(false);
        return false; // calibrate 
    }

    static bool penUp(){
        instructionLed.setState(true);
        display.display_text("PNUP");

        servoDriver.set_servo_angle(0, 30); // set "DO"

        display.display_text("----");
        instructionLed.setState(false);
        return false;
    }
    
    static bool penDown(){
        instructionLed.setState(true);
        display.display_text("PNDN");

        servoDriver.set_servo_angle(0, 0);

        display.display_text("----");
        instructionLed.setState(false);
        return false;
    }


};

pair<string, vector<float>> get_instruction_details(string instruction){
	// return string Instruction type, int* args4

	istringstream iss(instruction);
	vector<string> parts;
	vector<float> arguments;// store
	string part;

	string instruction_type; // first object in parts
	int parameters_size;

	while (iss >> part) {   // splits on whitespace by default
		parts.push_back(part);
	}

	instruction_type = parts[0];
	parameters_size = parts.size() - 1; // ignore the firts part

	for (int i = 1; i<parameters_size+1;i++) { // shift i by +1, so i can acces vector[i] ang skip the first element
		// convert str argumetents to floats
		arguments.push_back(stof(parts[i]));
	}
	/*
	for (const auto&  : words) {

		cout << w << "\n";
	}
	*/
	return {instruction_type, arguments};
}

// stuff for CDC full string recive
char rx_buf[BUF_MAX_LEN];
int rx_pos = 0;
int c;

//=============================================================

// send message to rsb, false=good, true=unusable
void confirm_recive(bool state){
    // false = all good
    // true error
    printf("%d\n", state); // dont forget to end message by '\n'
}

// wait for connection
void waitForCDC(){
    while (!stdio_usb_connected()) {
        sleep_ms(100);
    }
}

string instructionType;
vector<float> instructionArgunments;

void process_received(const string buf, int len) {
    // return false (0): the message is OK 
    // return true  (1): the message is unsable
    // handle complete message (null-terminated)
    

    auto instructionDetails = get_instruction_details(buf);

    instructionType         = instructionDetails.first;
    instructionArgunments   = instructionDetails.second;
    
    // check instruction usability
    
    // state of recived message
    bool recivedMessageState = false;

    if (INSTRUCTION_SIZES.count(instructionType) == 0){ //check if instruction is valid, if 1=false, 0=true
        recivedMessageState = true;
    }    
    if (INSTRUCTION_SIZES.at(instructionType) != (instructionArgunments.size())){ //check arguments size
        recivedMessageState = true;

    }

    // send out the state of recived message
    confirm_recive(recivedMessageState);
    

    if (recivedMessageState) return; // an error has happened

    // paths to different instructions
    bool instructionFinished;
    

    if          (instructionType=="MOV"){
    
        instructionFinished = Instructions::move(instructionArgunments[0], instructionArgunments[1]);
    
    } else if   (instructionType=="CLB"){
        // calibrate
        instructionFinished = Instructions::calibrate();

    } else if   (instructionType=="WAT"){
        // wait x seconds
        instructionFinished = Instructions::wait(instructionArgunments[0]);

    } else if (instructionType=="PUP"){

        instructionFinished = Instructions::penUp();

    } else if (instructionType=="PDN"){

        instructionFinished = Instructions::penDown();
    } 


    // send out if the instruction was run wihtout problems, false=good, true=unusable 
    confirm_recive(instructionFinished);
}

// main functions:

void CDC_loop(){
    // get full buffer
    while (true) {
        c = getchar_timeout_us(0);
        
        if (c == PICO_ERROR_TIMEOUT){ 
            break; // no more data, or no data to start with
        }
        if (rx_pos < BUF_MAX_LEN - 1) {
            rx_buf[rx_pos++] = (char)c;
        }
        // optional: detect end-of-line to process early, should allways be the case
        if (c == '\n' || c == '\r') {
            break;
        }
    }

    // work with recived string
    if (rx_pos > 0) {
        rx_buf[rx_pos] = '\0';    // null terminate
        
        // convert char* to std::string
        string message(rx_buf);

        // save the state, false=good, true=unusable
        process_received(message, rx_pos);
        
        // reset for next message
        rx_pos = 0;
    }
}

int main()
{
    if (true){ // for editor, can be hidden
    
    stdio_init_all();


    // Timer example code - This example fires off the callback after 2000ms
    add_alarm_in_ms(2000, alarm_callback, NULL, false);
    // For more examples of timer use see https://github.com/raspberrypi/pico-examples/tree/master/timer

    printf("System Clock Frequency is %d Hz\n", clock_get_hz(clk_sys));
    printf("USB Clock Frequency is %d Hz\n", clock_get_hz(clk_usb));
    // For more examples of clocks use see https://github.com/raspberrypi/pico-examples/tree/master/clocks
    }

    display.display_text("----");

    while (true) { // CDC loop
        CDC_loop();
        sleep_ms(1); // bottle neck, ignore for now
    }   
}