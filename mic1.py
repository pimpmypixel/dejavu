import json, warnings
warnings.filterwarnings("ignore")

from dejavu import Dejavu
from dejavu.recognize import MicrophoneRecognizer

with open("bassment.cnf") as f:
    config = json.load(f)

if __name__ == '__main__':
    djv = Dejavu(config)
    secs = 1
    song = djv.recognize(MicrophoneRecognizer, seconds=secs)
    if song is None:
        print "Nothing recognized"
    else:
        print "Recognized from mic with %d seconds: %s\n" % (secs, song)
