// Header file for input output functions
// do the pico code here
/*
will run a while (1) loop reciving and sending data thru the usb port (for now) to raspberry pi
drive the TMCs 2209 drivers real time (same time data send)
*/
#include <stdio.h>

// Main function: entry point for execution
int main() {
    int i;

    // Writing print statement to print hello world
    for (i = 0; i < 1000; i++){
        printf("Hello World");

    }

    return 0;
}