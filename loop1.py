from memory_profiler import profile
@profile
import json
import time
import warnings
warnings.filterwarnings("ignore")

from dejavu import Dejavu
from dejavu.recognize import MicrophoneRecognizer

with open("bassment.cnf") as f:
    config = json.load(f)

if __name__ == '__main__':
    djv = Dejavu(config)
    secs = 2
    wait = secs
    while True:
        song = djv.recognize(MicrophoneRecognizer, seconds=secs)
        if song is None:
            print "Nothing recognized"
        else:
            print "Recognized from mic with %d seconds: %s\n" % (secs, song)
        time.sleep(wait)
