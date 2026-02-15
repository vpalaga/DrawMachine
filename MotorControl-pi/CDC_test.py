from CDC_send import Transmiter
import time
from random_word import RandomWords
r = RandomWords()

# Return a single random word

transm = Transmiter()

while True:
    responce = transm.send(r.get_random_word() + "\n")

    print(responce)
    time.sleep(.01)
