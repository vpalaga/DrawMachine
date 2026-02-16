from CDC_send import Transmiter
import time

# Return a single random word

transm = Transmiter()

try:
    while True:
        recive_responce = transm.send_and_recive("WAT 3" + "\n")
        print("recive " + str(recive_responce))

        finish_state = transm.send_and_recive(None)
        print("finish " + str(finish_state))

        time.sleep(1)
finally:
    transm.__deinit__()
