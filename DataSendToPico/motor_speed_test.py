from DataSendToPico.src.CDC_send import Transmitter
import time

transmitter = Transmitter(console=False)

def send(m:str):
    start_time = time.time()
    receive_response = transmitter.send_and_receive(m + "\n")
    print("receive " + str(receive_response))

    finish_state = transmitter.send_and_receive(None)
    print("finish " + str(finish_state) + " program time: " + str(
        round((time.time() - start_time), ndigits=5)) + " seconds")

n = 0
while True:
    m = input("m: ").strip()
    if m == "q":
        break

    send(f"SMS 60 {m}")

    send("HCB")
    send("PDN")
    send("PUP")

    n+=1

transmitter.__deinit__()
