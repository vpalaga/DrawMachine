#include <stdio.h>
#include <string>
#include <vector>
#include <sstream>
#include <map>
#include <math.h>
#include <cmath>
#include <cstdint>

#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/timer.h"
#include "hardware/clocks.h"
#include "hardware/i2c.h"

#include "algorithm"

#include "drivers/HW069.h"
#include "drivers/Led.h"
#include "drivers/StepperDriver.h" 
#include "drivers/SwitchButton.h"
#include "drivers/Stepper.h"


using namespace std;


int64_t alarm_callback(alarm_id_t id, void *user_data) {
    // Put your timeout handler code in here
    return 0;
}


// end swich pins
// deifne the GPIO ports of the draw swiches terminals
// both thru swich to GND (pin 33, one above)


// us sleep between steps

// LEDs wire to GND (pin 23)
const int LED_SYSTEM = 25;

const int BUF_MAX_LEN = 128;
const int INSTRUCION_TIMEOUT_MS = 3000; 

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

uint8_t consoleEnabled = 2; // 2 for unassigned 1 true 0 false

// instruction type vs arguments
const map<string, int> INSTRUCTION_SIZES = {
    {"MOV", 2},// xsteps ysteps
    {"CLB", 0},// 
    {"WAT", 1},// seconds
    {"SCA", 2}, // channel, angle
    {"SCM", 1} // mode (0,1,2)
};
//=============================================================

// display object
HW069 display(14, 15);

// manual control swiches
SwitchButton mSwich_XP(5);
SwitchButton mSwich_XM(4);
SwitchButton mSwich_YP(3);
SwitchButton mSwich_YM(2);

SwitchButton mSwich_B1(6);
SwitchButton mSwich_B2(7);

// instruction led, when doing instruction than, on
Led instructionLed(28);
Led ledConsoleMode(17);
Led onLed(16);

// driver: xstp xdir ystp ydir
StepperDriver stepper_driver(19, 18, 21, 20);

// end swiches, use with calibrate
SwitchButton xSwich(26); // GPIo 26
SwitchButton ySwich(27); // GPIO 27


class Instructions{
public:
    static bool wait(float seconds){
        display.display_text("WAIT");

        sleep_ms(seconds*1000); // make into seconds

        display.display_text("----");
        return false;
    }

    static bool move(int x, int y){
        display.display_text("MOVE");

        stepper_driver.move(x, y);

        display.display_text("----");
        return false; // move 
    }

    static bool calibrate(){
        display.display_text("CALB");

        while ((!xSwich.getSwichState()) && (!ySwich.getSwichState())){ // dosnt conduct
            // i dont think a sleep is needed here, since 900 steps = 1mm move, so should be more than enough time to stop
            stepper_driver.move(-1, -1); // move one step x back (-)
        }
        while (!xSwich.getSwichState()){ // dosnt conduct
            // i dont think a sleep is needed here, since 900 steps = 1mm move, so should be more than enough time to stop
            stepper_driver.move(-1, 0); // move one step x back (-)
        }
        while (!ySwich.getSwichState()){ // dosnt conduct
            // i dont think a sleep is needed here, since 900 steps = 1mm move, so should be more than enough time to stop
            stepper_driver.move(0, -1); // move one step x back (-)
        }

        // reset stepper pos
        stepper_driver.pos_reset();

        display.display_text("----");
        return false; // calibrate 
    }

    static bool servo_angle(uint8_t channel, float angle){
        display.display_text("SANG");

        // DOOOOOO this to move the pen up

        display.display_text("----");
        return false;
    }
    static bool set_instruction_mode(uint8_t mode){
        consoleEnabled = mode;
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

    } else if (instructionType=="SCA"){
        // channel, angle
        instructionFinished = Instructions::servo_angle((uint8_t)instructionArgunments[0],instructionArgunments[1]);
        ;
    } else if (instructionType=="SCM"){
        // mode
        instructionFinished = Instructions::set_instruction_mode((uint8_t)instructionArgunments[0]);
        ;
    }


    // send out if the instruction was run wihtout problems, false=good, true=unusable 
    confirm_recive(instructionFinished);
}

void manual_instruction(){
    int8_t x_move = 0;
    int8_t y_move = 0;

    if(mSwich_XP.getSwichState()){
        x_move++;
        if(consoleEnabled == 1){
            printf("B1 (xp): pressed");
        }    
    }

    if(mSwich_XM.getSwichState()){
        x_move--;
        if(consoleEnabled == 1){
            printf("B2 (xm): pressed");
        }    
    }

    if(mSwich_YP.getSwichState()){
        y_move++;
        if(consoleEnabled == 1){
            printf("B3 (yp): pressed");
        }    
    }

    if(mSwich_YM.getSwichState()){
        y_move--;
        if(consoleEnabled == 1){
            printf("B4 (ym): pressed");
        }    
    }

    // undefined
    if(mSwich_B1.getSwichState()){ // print head position
        if (consoleEnabled == 1){
            stepper_driver.printPosToTermial();
            printf("B5: pressed");
            sleep_ms(700);
        }
    }

    if(mSwich_B2.getSwichState()){
        if(consoleEnabled){
            printf("B6: pressed");
        }    
}

    // move the motors if needed
    if (x_move != 0 || y_move != 0){
        stepper_driver.move(x_move, y_move);
    }

    return;
}

// main functions:

bool CDC_loop(){
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
        process_received(message, rx_pos);

        // reset for next message
        rx_pos = 0;
        return true;
    }
    return false;
}


int time_from_last_inst;

int main()
{
    if (true){ // for editor, can be hidden
    
    stdio_init_all();


    // Timer example code - This example fires off the callback after 2000ms
    add_alarm_in_ms(2000, alarm_callback, NULL, false);
    // For more examples of timer use see https://github.com/raspberrypi/pico-examples/tree/master/timer

    //printf("System Clock Frequency is %d Hz\n", clock_get_hz(clk_sys));
    //printf("USB Clock Frequency is %d Hz\n", clock_get_hz(clk_usb));
    // For more examples of clocks use see https://github.com/raspberrypi/pico-examples/tree/master/clocks
    }
    
    onLed.setState(true);
    display.display_text("8-- ");

    while (true) { // CDC loop
        
        if (CDC_loop()){time_from_last_inst=0;} else {time_from_last_inst++;}
        
        sleep_ms(1); // bottle neck, ignore for now

        if (time_from_last_inst > INSTRUCION_TIMEOUT_MS){
            // enable manual control
            instructionLed.setState(false);
            manual_instruction();
        }
        
        // reset instruction led after reciving an istructon
        if (time_from_last_inst == 0){instructionLed.setState(true);}
        if (consoleEnabled != ledConsoleMode.state && consoleEnabled != 2)   {ledConsoleMode.setState(consoleEnabled);}
    }   
}