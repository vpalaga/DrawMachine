from CDC_send import Transmiter
import time
import time

transm = Transmiter()

try:
    while True:
        start_time = time.time()

        receive_response = transm.send_and_receive(f"CLB\n")
        print("recive " + str(receive_response))

        finish_state = transm.send_and_receive(None)
        print("finish " + str(finish_state) + " program time: " + str(round((time.time() - start_time)*1000, ndigits=5)) + " miliseconds")

        time.sleep(1)
finally:
    transm.__deinit__()
