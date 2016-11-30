import json
import os.path
import warnings
import argparse
import sys
import logging
import time
import MySQLdb
import MySQLdb.cursors
from datetime import datetime
from dejavu import Dejavu
from dejavu.recognize import MicrophoneRecognizer

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")
db = "conf/database.json"
config = {}

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()

    levels = [logging.NOTSET, logging.INFO, logging.DEBUG]
    level_index = min(len(levels) - 1, args.verbose)
    level = levels[level_index]  # capped to number of levels
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")

    with open(os.path.dirname(__file__) + db) as f:
        config['database'] = json.load(f)
        con = MySQLdb.connect(
            config.get('database').get('host'),
            config.get('database').get('user'),
            config.get('database').get('passwd'),
            config.get('database').get('db'),
            cursorclass=MySQLdb.cursors.DictCursor
        )
        cur = con.cursor()
        cur.execute("SELECT * FROM `configurations` WHERE id = (SELECT active FROM `states` ORDER BY id DESC limit 1)")
        config['fingerprint'] = cur.fetchone()

        config['fingerprint']['amp_min'] = 10
        config['fingerprint']['plot'] = 0
        config['verbose'] = False

        config['soundcard'] = {
            "chunksize": 8096,
            "test": 1
        }

        logging.info("Using config '" + config['fingerprint']['name'] + "'")
        if args.verbose:
            config['verbose'] = True

        if config['verbose']:
            import pyaudio

            p = pyaudio.PyAudio()
            for i in range(0, 3):
                if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    logging.debug("Input Device id " + str(i) + " - " +
                                  p.get_device_info_by_host_api_device_index(0, i).get('name'))

            devinfo = p.get_device_info_by_index(1)
            logging.info("Selected device is " + str(devinfo.get('name')))
            if p.is_format_supported(44100.0,  # Sample rate
                                     input_device=devinfo["index"],
                                     input_channels=devinfo['maxInputChannels'],
                                     input_format=pyaudio.paInt16):
                logging.debug('Hardware config supported')
            else:
                logging.info('Hardware config not supported')
                sys.exit(1)

        if __name__ == '__main__':
            djv = Dejavu(config)
            a = datetime.now()
            listen = 2
            pause = 1
            it = 1
            try:
                while True:
                    song = djv.recognize(MicrophoneRecognizer, seconds=listen)
                    if song is None:
                        if args.verbose:
                            logging.info(str(it) + ". Nothing recognized")
                        else:
                            print str(it) + " - Nothing recognized"
                    else:
                        if args.verbose:
                            logging.info(str(it) + ". Recognized from mic with %d seconds: %s\n" % (listen, song))
                        else:
                            print str(it) + " - Recognized from mic with %d seconds: %s\n" % (listen, song)
                    it += 1
                    time.sleep(pause)
            except KeyboardInterrupt:
                pass

except MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit(1)
