import json
import warnings
import sys
import time
from datetime import datetime
import MySQLdb
import MySQLdb.cursors

from dejavu import Dejavu
from dejavu.recognize import MicrophoneRecognizer


warnings.filterwarnings("ignore")
db = "database.json"
config = {}
"""
Get json file with database connection info
to query the current config vars
"""

try:
    with open(db) as f:
        config['database'] = json.load(f)
        con = MySQLdb.connect(
            config.get('database').get('host'),
            config.get('database').get('user'),
            config.get('database').get('passwd'),
            config.get('database').get('db'),
            cursorclass=MySQLdb.cursors.DictCursor
        )
        cur = con.cursor()
        cur.execute("SELECT active FROM `states` ORDER BY id DESC limit 1")
        active = cur.fetchone()
        cur.execute("SELECT * FROM `configurations` WHERE id = " + str(active['active']))
        config['fingerprint'] = cur.fetchone()


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

except MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit(1)
