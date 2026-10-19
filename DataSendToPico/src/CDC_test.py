from CDC_send import Transmitter
import time

transmitter = Transmitter(console=False)

#transmitter.console(switch_beep=False)

i = 3
try:
    
    while True:
        m = input("m: ").strip()
        print("...")
        if m == "q":
            break
        start_time = time.time()

        receive_response = transmitter.send_and_receive(m + "\n")
        print("receive " + str(receive_response))

        finish_state = transmitter.send_and_receive(None)
        print("finish " + str(finish_state) + " program time: " + str(round((time.time() - start_time), ndigits=5)) + " seconds")

finally:
    transmitter.__deinit__()
