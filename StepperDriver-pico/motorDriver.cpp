#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/timer.h"
#include "hardware/clocks.h"
#include "algorithm"
#include <string>
#include <vector>
#include <sstream>
#include <map>
#include <math.h>

using namespace std;

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
const int LED_INSTRUCTION_PIN = 17;
const int LED_2_PIN = 16;


// CDC buffer max len, removed static 16,2,26
const int BUF_MAX_LEN = 128;

// instruction type vs atguments
const map<string, int> INSTRUCTION_SIZES = {
    {"MOV", 2},
    {"CLB", 0},
    {"WAT", 1}
};
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

// end swiches, use with calibrate
Swich xSwich(X_SWICH_GPIO); // GPIo 26
Swich ySwich(Y_SWICH_GPIO); // GPIO 27

// instruction led, when doing instruction than, on
LED instructionLed(LED_INSTRUCTION_PIN);

// driver
StepperDriver driver;

class Instructions{
public:
    static bool wait(float seconds){
        instructionLed.setState(true);

        sleep_ms(seconds*1000); // make into seconds

        instructionLed.setState(false);
        return false;
    }

    static bool move(int x, int y){
        instructionLed.setState(true);

        driver.move(x, y);

        instructionLed.setState(false);
        return false; // move 
    }

    static bool calibrate(){
        instructionLed.setState(true);

        while (!xSwich.getSwichState()){ // dosnt conduct
            driver.move(1, 0); // move one step x
        }

        instructionLed.setState(false);
        return false; // calibrate 
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

    LED led(1); // for testing, remove later
    
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
        // move
        instructionFinished = Instructions::move(instructionArgunments[0], instructionArgunments[1]);
    
    } else if   (instructionType=="CLB"){
        // calibrate
        instructionFinished = Instructions::calibrate();

    } else if   (instructionType=="WAT"){
        // wait x seconds
        instructionFinished = Instructions::wait(instructionArgunments[0]);
    }

    // send out if the instruction was run wihtout problems, false=good, true=unusable 
    confirm_recive(instructionFinished);
}

// main function:

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
    //Stepper xStepper(X_STP_STEPPER_PIN, X_DIR_STEPPER_PIN, 1000);

    while (true) { // CDC loop
        CDC_loop();
        sleep_ms(1); // bottle neck, ignore for now
    }
    
}
