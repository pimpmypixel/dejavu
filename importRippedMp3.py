import warnings
import json
warnings.filterwarnings("ignore")

from dejavu import Dejavu
from dejavu.recognize import FileRecognizer, MicrophoneRecognizer
with open("settings.json") as f:
    config = json.load(f)
    config['database']['db'] = 'pi1'

if __name__ == '__main__':
	djv = Dejavu(config)
	djv.fingerprint_directory("mp3", [".mp3"])
