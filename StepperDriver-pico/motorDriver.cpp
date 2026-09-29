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

#include "drivers/Led.h"
#include "drivers/StepperDriver.h" 
#include "drivers/SwitchButton.h"
#include "drivers/Stepper.h"

using namespace std;

int64_t alarm_callback(alarm_id_t id, void *user_data) {
    // Put your timeout handler code in here
    return 0;
}

const int BUF_MAX_LEN = 128;

uint8_t consoleEnabled = 2; // 2 for unassigned 1 true 0 false

// instruction type vs arguments
const map<string, int> INSTRUCTION_SIZES = {
    {"MOV", 2},// xsteps ysteps
    {"CLB", 0},// 
    {"WAT", 1},// seconds
    {"PUP", 0}, // 
    {"PDN", 0}, // 
    {"SCM", 1} // mode (0,1,2)
};
//=============================================================

// manual control swiches
SwitchButton mSwich_XP(22);
SwitchButton mSwich_XM(21);
SwitchButton mSwich_YP(20);
SwitchButton mSwich_YM(19);
SwitchButton mSwich_B1(18);
SwitchButton mSwich_B2(17);

// end swiches, use with calibrate
SwitchButton xSwich(11);
SwitchButton ySwich(7);
SwitchButton zSwich(2); 

// leds
Led instructionLed(15);
Led ledConsoleMode(14);

// driver: xstp xdir ystp ydir
Stepper::stepper_pins x_stepper_pins = {4, 3, 5};
Stepper::stepper_pins y_stepper_pins = {8, 6, 9};
Stepper::stepper_pins z_stepper_pins = {13, 12, 10};

struct Settings {
    const uint16_t z_stepper_us_sleep = 50; 
    const int pen_up_down_steps = 300; // needs to be tested 
    const int INSTRUCION_TIMEOUT_MS = 3000; 
    const uint16_t x_y_halfcycle_us_sleep = 50;
}settings;


StepperDriver stepper_driver(x_stepper_pins, x_stepper_pins);
Stepper z_stepper(z_stepper_pins);

void z_stepper_calibrate(){
    while (!zSwich.getSwichState()){ // dosnt conduct
        // i dont think a sleep is needed here, since 900 steps = 1mm move, so should be more than enough time to stop
        // move into z+ direction
        z_stepper.move(1, settings.z_stepper_us_sleep); // move one step x back (-)
    }
    stepper_driver.is_pen_down = false;
}

class Instructions{
public:
    static bool wait(float seconds){

        sleep_ms(seconds*1000); // make into mini seconds

        return false;
    }

    static bool move(int x, int y){

        stepper_driver.enable(true);
        stepper_driver.move(x, y);
        
        return false; // move 
    }

    static bool calibrate(){

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

        // z calib
        z_stepper_calibrate();

        return false; // calibrate 
    }

    static bool pen_up(){
        // check last known pen pos
        if (!stepper_driver.is_pen_down){return true;}

        // move +z direction
        z_stepper.move(settings.pen_up_down_steps, settings.z_stepper_us_sleep);
        stepper_driver.is_pen_down = false;

        return false;
    }
    
    static bool pen_down(){
        // check last known pen pos
        if (stepper_driver.is_pen_down){return true;}

        // move -z direction
        z_stepper.move(- settings.pen_up_down_steps, settings.z_stepper_us_sleep);
        stepper_driver.is_pen_down = true;

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

    } else if (instructionType=="PUP"){
        // channel, angle
        instructionFinished = Instructions::pen_up();
    } else if (instructionType=="PDN"){
        // channel, angle
        instructionFinished = Instructions::pen_down();  
    
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
            printf("B2 (xm): pressed\n");
            printf("x: %d\n", xSwich.getSwichState());
            printf("y: %d\n", ySwich.getSwichState());
            sleep_ms(20);
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
        stepper_driver.enable(true);
        stepper_driver.move(x_move, y_move);
        stepper_driver.enable(false);
        
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
    stdio_init_all();
    // set to thing in settings
    stepper_driver.motor_sleep_us = settings.x_y_halfcycle_us_sleep;

    while (true) { // CDC loop
        
        if (CDC_loop()){time_from_last_inst=0;} else {time_from_last_inst++;}
        
        sleep_ms(1); // bottle neck, ignore for now

        if (time_from_last_inst > settings.INSTRUCION_TIMEOUT_MS){
            // enable manual control
            instructionLed.setState(false);
            stepper_driver.enable(false);

            manual_instruction();

        } 
        
        // reset instruction led after reciving an istructon
        if (time_from_last_inst == 0){instructionLed.setState(true);}
        if (consoleEnabled != ledConsoleMode.state && consoleEnabled != 2)   {ledConsoleMode.setState(consoleEnabled);}
    }   
}