import json
import time
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

from dejavu import Dejavu
from dejavu.recognize import MicrophoneRecognizer

with open("settings.json") as f:
    config = json.load(f)

if __name__ == '__main__':
    djv = Dejavu(config)
    a = datetime.now()
    listen = 2
    pause = 1
    it = 1
    try:
        while True:
            song = djv.recognize(MicrophoneRecognizer, seconds=listen)
            b = datetime.now() - a
            if song is None:
                print str(b) + " - " + str(it) + ". Nothing recognized"
            else:
                print str(b) + " - " + str(it) + ". Recognized from mic with %d seconds: %s\n" % (listen, song)
            it += 1
            a = datetime.now()
            time.sleep(pause)
    except KeyboardInterrupt:
        pass