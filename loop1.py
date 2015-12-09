import json
import time
import warnings
warnings.filterwarnings("ignore")

from dejavu import Dejavu
from dejavu.recognize import MicrophoneRecognizer

with open("settings.json") as f:
    config = json.load(f)

if __name__ == '__main__':
    djv = Dejavu(config)
    secs = 2
    try:
        while True:
            song = djv.recognize(MicrophoneRecognizer, seconds=secs)
            if song is None:
                print "Nothing recognized"
            else:
                print "Recognized from mic with %d seconds: %s\n" % (secs, song)
            time.sleep(2)
    except KeyboardInterrupt:
        pass