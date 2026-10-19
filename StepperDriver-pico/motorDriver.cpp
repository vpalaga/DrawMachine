#include <stdio.h>
#include <string>
#include <vector>
#include <sstream>
#include <map>
#include <math.h>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <algorithm>

#include "pico/stdlib.h"
#include "hardware/timer.h"
#include "hardware/clocks.h"

#include "drivers/Led.h"
#include "drivers/StepperDriver.h" 
#include "drivers/SwitchButton.h"
#include "drivers/Head.h"

using namespace std;

int64_t alarm_callback(alarm_id_t id, void *user_data) {
    // Put your timeout handler code in here
    return 0;
}

const int BUF_MAX_LEN = 128;

uint8_t consoleEnabled = 2; // 2 for unassigned 1 true 0 false

// instruction type vs arguments
const map<string, size_t> INSTRUCTION_SIZES = {
    {"MOV", 2},// xsteps ysteps
    {"CLB", 0},// 
    {"WAT", 1},// seconds
    {"PUP", 0}, // 
    {"PDN", 0}, // 
    {"SCM", 1}, // mode (0,1,2)
    {"SMS", 2}, // set motor speed (xy, z)
    {"HCB", 0} // head calibrate
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
const int z_endstop_pin = 2;

// leds
Led instructionLed(15);
Led ledConsoleMode(14);

// driver: step dir enable
Stepper::stepper_pins x_stepper_pins = {13, 12, 10};
Stepper::stepper_pins y_stepper_pins = {8, 6, 9};
Stepper::stepper_pins z_stepper_pins = {4, 3, 5}; 

struct Settings {
    const int pen_up_down_steps = 6500; // needs to be tested 
    const int INSTRUCTION_TIMEOUT_MS = 3000;
    const uint16_t x_y_halfcycle_us_sleep = 75;
    // safety limits so calibration can never run forever if a switch is missing / miswired
    const int max_calibrate_steps_xy = 400000;
    const int max_calibrate_steps_z  = 50000;
}settings;


StepperDriver stepper_driver(x_stepper_pins, y_stepper_pins);
Head head(z_stepper_pins, z_endstop_pin, ledConsoleMode);

class Instructions{
public:
    static bool wait(float seconds){

        sleep_ms((uint32_t)(seconds*1000)); // make into mini seconds

        return false;
    }

    static bool move(int x, int y){

        stepper_driver.move(x, y);
        
        return false; // move 
    }

    static bool calibrate(){
        int guard = 0;

        while ((!xSwich.getSwichState()) && (!ySwich.getSwichState())){ // dosnt conduct
            if (++guard > settings.max_calibrate_steps_xy){stepper_driver.enable(false); return true;}
            stepper_driver.move(-1, -1); // move one step x and y back (-)
        }
        guard = 0;
        while (!xSwich.getSwichState()){ // dosnt conduct
            if (++guard > settings.max_calibrate_steps_xy){stepper_driver.enable(false); return true;}
            stepper_driver.move(-1, 0); // move one step x back (-)
        }
        guard = 0; 

        while (!ySwich.getSwichState()){ // dosnt conduct
            if (++guard > settings.max_calibrate_steps_xy){stepper_driver.enable(false); return true;}
            stepper_driver.move(0, -1); // move one step y back (-)
        }
        // reset stepper pos
        stepper_driver.pos_reset();

        // z calib

        return head.calibrate(settings.max_calibrate_steps_z);
    }

    static bool head_calibrate(){
        return head.calibrate(settings.max_calibrate_steps_z);
    }

    static bool pen_up(){
        return head.penUp(settings.pen_up_down_steps);
    }
    
    static bool pen_down(){
        return head.penDown(settings.pen_up_down_steps);
    }

    static bool set_instruction_mode(uint8_t mode){
        consoleEnabled = mode;
        return false;
    }

    static bool set_motor_speed(int xy_sleep_us, int z_sleep){
        stepper_driver.motor_sleep_us = xy_sleep_us;
        head.setSpeed(z_sleep);
        return false;
    }
};

// split a line into instruction type + float arguments.
// returns false if the line is empty or an argument is not a valid number (never throws).
static bool parse_instruction(const string& line, string& instruction_type, vector<float>& arguments){
    istringstream iss(line);
    string part;

    arguments.clear();

    if (!(iss >> instruction_type)) return false; // empty / whitespace only

    while (iss >> part) {   // splits on whitespace by default
        char* end = nullptr;
        float value = strtof(part.c_str(), &end);
        if (end == part.c_str() || *end != '\0') return false; // not a number
        arguments.push_back(value);
    }
    return true;
}

// stuff for CDC full string recive
char rx_buf[BUF_MAX_LEN];
int rx_pos = 0;

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

void process_received(const string& buf, int len) {
    // return false (0): the message is OK 
    // return true  (1): the message is unsable
    string instructionType;
    vector<float> args;

    // state of recived message
    bool recivedMessageState = false;

    if (!parse_instruction(buf, instructionType, args)){
        recivedMessageState = true; // empty line or bad number
    } else {
        auto it = INSTRUCTION_SIZES.find(instructionType);
        if (it == INSTRUCTION_SIZES.end()){        // unknown instruction
            recivedMessageState = true;
        } else if (it->second != args.size()){ // wrong argument count
            recivedMessageState = true;
        }
    }

    // send out the state of recived message
    confirm_recive(recivedMessageState);

    if (recivedMessageState) return; // an error has happened

    bool failed = true;  // default: unknown instruction = unusable

    if (instructionType == "MOV") {
        failed = Instructions::move((int)args[0], (int)args[1]);
    } else if (instructionType == "CLB") {
        failed = Instructions::calibrate();
    } else if (instructionType == "WAT") {
        failed = Instructions::wait(args[0]);
    } else if (instructionType == "PUP") {
        failed = Instructions::pen_up();
    } else if (instructionType == "PDN") {
        failed = Instructions::pen_down();
    } else if (instructionType == "SCM") {
        failed = Instructions::set_instruction_mode((uint8_t)args[0]);
    } else if (instructionType == "SMS") {
        failed = Instructions::set_motor_speed((int)args[0], (int)args[1]);
    } else if (instructionType == "HCB") {
        failed = Instructions::head_calibrate();
    }

    // send out if the instruction was run wihtout problems, false=good, true=unusable 
    confirm_recive(failed);
}

void manual_instruction(){
    int8_t x_move = 0;
    int8_t y_move = 0;

    if(mSwich_XP.getSwichState()){
        x_move++;
        if(consoleEnabled == 1){
            printf("B1 (xp): pressed\n");
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
            printf("B3 (yp): pressed\n");
        }    
    }

    if(mSwich_YM.getSwichState()){
        y_move--;
        if(consoleEnabled == 1){
            printf("B4 (ym): pressed\n");
        }    
    }

    if(mSwich_B1.getSwichState()){ // print head position
        if (consoleEnabled == 1){
            stepper_driver.printPosToTermial();
            printf("B5: pressed\n");
            sleep_ms(700);
        }
    }

    if(mSwich_B2.getSwichState()){
        if(consoleEnabled == 1){
            printf("B6: pressed\n");
        }    
    }

    // move the motors if needed
    if (x_move != 0 || y_move != 0){
        stepper_driver.move(x_move, y_move);
    }

    return;
}

// main functions:

// returns true when a complete line was received and processed
bool CDC_loop(){
    bool lineComplete = false;

    // read everything that is available
    while (true) {
        int ch = getchar_timeout_us(0);
        
        if (ch == PICO_ERROR_TIMEOUT){ 
            break; // no more data, or no data to start with
        }
        if (ch == '\n' || ch == '\r') {
            if (rx_pos == 0) continue; // blank line / second half of "\r\n": ignore
            lineComplete = true;       // end of message
            break;
        }
        if (rx_pos < BUF_MAX_LEN - 1) {
            rx_buf[rx_pos++] = (char)ch;
        }
    }

    // only process full lines, never a half-received one
    if (!lineComplete) return false;

    rx_buf[rx_pos] = '\0';    // null terminate
    
    // convert char* to std::string
    string message(rx_buf);
    int len = rx_pos;

    // reset for next message
    rx_pos = 0;

    process_received(message, len);
    return true;
}

int main()
{
    stdio_init_all();
    // set to thing in settings
    stepper_driver.motor_sleep_us = settings.x_y_halfcycle_us_sleep;

    // blink for startup
    for (int i = 0; i<6; i++){ledConsoleMode.toggleLed();sleep_ms(200);}

    // real time based timeout (instead of counting loop iterations)
    absolute_time_t last_instruction_time = get_absolute_time();
    const int64_t timeout_us = (int64_t)settings.INSTRUCTION_TIMEOUT_MS * 1000;

    while (true) { // CDC loop
        
        if (CDC_loop()){last_instruction_time = get_absolute_time();}

        sleep_ms(1); // bottleneck, ignore for now

        if (absolute_time_diff_us(last_instruction_time, get_absolute_time()) > timeout_us){
            // enable manual control
            instructionLed.setState(false);
            stepper_driver.enable(false);

            //manual_instruction();
        } else {
            // an instruction was received recently
            instructionLed.setState(true);
        }
        
        if (consoleEnabled != ledConsoleMode.state && consoleEnabled != 2)   {ledConsoleMode.setState(consoleEnabled);}
    }   
}