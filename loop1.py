import json
warnings.filterwarnings("ignore")

from PROJEKT2.dejavu import Dejavu
from PROJEKT2.dejavu.recognize import MicrophoneRecognizer

with open("dejavu.cnf.SAMPLE") as f:
    config = json.load(f)

if __name__ == '__main__':
    djv = Dejavu(config)
    secs = 5
    song = djv.recognize(MicrophoneRecognizer, seconds=secs)
    if song is None:
        print "Nothing recognized"
    else:
        print "Recognized from mic with %d seconds: %s\n" % (secs, song)
