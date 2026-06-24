#ifndef HW069_H
#define HW069_H

class HW069{
public:
    int CLK;
    int DIO;
    HW069(int CLK_init_,int DIO_init_);

    int int_to_segment(int i);
    int char_to_segment(char c);
    void tm_delay();
    void tm_start();
    void tm_stop();
    void tm_write(int data);
    void display_number(int num);
    void display_text(const char *s);
};

#endif
