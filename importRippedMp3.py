import warnings
import json
warnings.filterwarnings("ignore")

from dejavu import Dejavu
from dejavu.recognize import FileRecognizer, MicrophoneRecognizer
with open("bassment.cnf") as f:
    config = json.load(f)
    config['database']['db'] = 'dejavu2'

if __name__ == '__main__':
	djv = Dejavu(config)
	djv.fingerprint_directory("mp3/tv2", [".mp3"])
