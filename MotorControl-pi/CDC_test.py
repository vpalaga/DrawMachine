from CDC_send import Transmiter
import time
import time

transm = Transmiter()

inst = ["WAT 1\n","MOV 1800 1800\n","CLB\n"]

i = 0
try:
    while True:
        start_time = time.time()

        receive_response = transm.send_and_receive(inst[i])
        print("recive " + str(receive_response))

        finish_state = transm.send_and_receive(None)
        print("finish " + str(finish_state) + " program time: " + str(round((time.time() - start_time)*1000, ndigits=5)) + " miliseconds")

        i += 1
        if i>len(inst)-1:
            i=0
        
        time.sleep(1)
finally:
    transm.__deinit__()
