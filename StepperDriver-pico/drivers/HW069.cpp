#include "HW069.h"
#include "pico/stdlib.h"

HW069::HW069(int CLK_init_,int DIO_init_){
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
};

int HW069::int_to_segment(int i){
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
};

int HW069::char_to_segment(char c){
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
};

void HW069::tm_delay(){sleep_us(5);};

void HW069::tm_start(){
    gpio_set_dir(DIO, GPIO_OUT);
    gpio_put(DIO, 1);
    gpio_put(CLK, 1);
    tm_delay();
    gpio_put(DIO, 0);
};

void HW069::tm_stop(){
    gpio_put(CLK, 0);
    tm_delay();
    gpio_put(DIO, 0);
    tm_delay();
    gpio_put(CLK, 1);
    tm_delay();
    gpio_put(DIO, 1);
};

void HW069::tm_write(int data){
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
};
void HW069::display_number(int num){
    int digits[4] = {
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
};
void HW069::display_text(const char *s){
    int segs[4] = {0,0,0,0};
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
};

