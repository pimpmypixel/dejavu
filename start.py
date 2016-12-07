#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import os.path
import warnings
import argparse
import sys
import logging
import time
import MySQLdb
import MySQLdb.cursors
from ctypes import *
from datetime import datetime
from dejavu import Dejavu
from dejavu.recognize import MicrophoneRecognizer

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")
db = os.path.dirname(__file__) + "/conf/database.json"
log = os.path.dirname(__file__) + "/log/log.log"
config = {}

def getConguration():
	with open(db) as f:
		logging.debug("Getting config")
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
		logging.debug(config)
		return config

try:
	parser = argparse.ArgumentParser()
	parser.add_argument('-v', '--verbose', action='count', default=0)
	args = parser.parse_args()

	levels = [logging.WARNING, logging.INFO, logging.DEBUG]
	level_index = min(len(levels) - 1, args.verbose)
	level = levels[level_index]  # capped to number of levels
	logging.basicConfig(filename=log,
						filemode='a',
						format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
						datefmt='%H:%M:%S',
						level=level)
	config = getConguration()
	logging.info("Using config '" + config['fingerprint']['name'] + "'")

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
	logging.info("Error %d: %s" % (e.args[0], e.args[1]))
	sys.exit(1)
