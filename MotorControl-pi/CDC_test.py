from CDC_send import Transmiter
import time
import time

transm = Transmiter()
wait = 1

try:
    while True:
        start_time = time.time()

        receive_response = transm.send_and_recive("WAT " + str(wait) + "\n")
        print("recive " + str(receive_response))

        finish_state = transm.send_and_recive(None)
        print("finish " + str(finish_state) + " program time: " + str(round((time.time() - start_time - wait)*1000, ndigits=5)) + " miliseconds")

        time.sleep(1)
finally:
    transm.__deinit__()
