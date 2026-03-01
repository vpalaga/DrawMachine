from CDC_send import Transmiter
import time
import time

transm = Transmiter(console=True)

inst = ["WAT 1\n",
        "MOV 10000 3000\n",
        "CLB\n",
        "SCA 0 90\n",   
        "SCA 0 -90\n",]

i = 3
try:
    transm.console()
    while True:
        start_time = time.time()

        receive_response = transm.send_and_receive(inst[1])
        print("recive " + str(receive_response))

        finish_state = transm.send_and_receive(None)
        print("finish " + str(finish_state) + " program time: " + str(round((time.time() - start_time), ndigits=5)) + " miliseconds")

        i += 1
        if i>len(inst)-1:
            i=3
        
        
        time.sleep(4)
finally:
    transm.__deinit__()
