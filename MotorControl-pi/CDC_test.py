from CDC_send import Transmiter
import time
from random_word import RandomWords
r = RandomWords()

# Return a single random word

transm = Transmiter()

try:
    while True:
        word = r.get_random_word()
        responce = transm.send(word + "\n")

        print(responce, word)
        time.sleep(.1)
finally:
    transm.__deinit__()
