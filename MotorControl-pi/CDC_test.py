from CDC_send import Transmitter
import time

transmitter = Transmitter(console=False)

inst = ["WAT 1\n",
        "MOV 10000 3000\n",
        "CLB\n",
        "SCA 0 90\n",   
        "SCA 0 -90\n",]

#transmitter.console()

i = 3
try:
    
    while True:
        m = input("m: ").strip()

        start_time = time.time()

        receive_response = transmitter.send_and_receive(m + "\n")
        print("receive " + str(receive_response))

        finish_state = transmitter.send_and_receive(None)
        print("finish " + str(finish_state) + " program time: " + str(round((time.time() - start_time), ndigits=5)) + " miliseconds")

finally:
    transmitter.__deinit__()
