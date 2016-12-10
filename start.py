#!/usr/bin/python
# -*- coding: utf-8 -*-
import json, os.path, warnings, argparse, sys, logging, threading, time, MySQLdb
import MySQLdb.cursors
from ctypes import *
from datetime import datetime
from dejavu import Dejavu
from dejavu.recognize import MicrophoneRecognizer
import CHIP_IO.GPIO as GPIO
import atexit
import netifaces as ni
import uuid
import ipgetter
import subprocess

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")
db = os.path.dirname(__file__) + "conf/database.json"
log = os.path.dirname(__file__) + "log/log.log"
config = {}


def getConguration():
	with open(db) as f:
		logging.debug("Getting config")
		config['database'] = json.load(f)
		try:
			con = MySQLdb.connect(
				config.get('database').get('host'),
				config.get('database').get('user'),
				config.get('database').get('passwd'),
				config.get('database').get('db'),
				cursorclass=MySQLdb.cursors.DictCursor
			)
			if (db):
				print "Connection successful"
				cur = con.cursor()
				cur.execute(
					"SELECT * FROM `configurations` WHERE id = (SELECT active FROM `states` ORDER BY id DESC limit 1)")
				config['fingerprint'] = cur.fetchone()
				config['session'] = uuid.uuid4()
				config['remote_ip'] = ipgetter.myip()
				config['vpn_ip'] = ni.ifaddresses('tun0')[2][0]['addr']
				config['fingerprint']['amp_min'] = 10
				config['fingerprint']['plot'] = 0
				config['verbose'] = False
				config['soundcard'] = {
					"chunksize": 8096,
					"test": 1
				}
				logging.debug(config)
				return config
			else:
				print "Connection unsuccessful"
		except MySQLdb.Error, e:
			print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
			print "MySQL Error: %s" % str(e)


def setupLed():
	print("Testing LED XIO-P0 for 3 seconds")
	GPIO.setup("XIO-P0", GPIO.OUT)
	GPIO.output("XIO-P0", GPIO.LOW)
	time.sleep(3)
	GPIO.output("XIO-P0", GPIO.HIGH)
	GPIO.cleanup()


def blinkLed():
	GPIO.setup("XIO-P0", GPIO.OUT)
	for j in range(1, 10):
		GPIO.output("XIO-P0", GPIO.LOW)
		time.sleep(.1)
		GPIO.output("XIO-P0", GPIO.HIGH)
		time.sleep(.1)
	GPIO.cleanup()
	return


def exit_handler(djv):
	print 'Session ended'
	djv.log_event(config['session'], config['vpn_ip'], config['remote_ip'], 'end')


def check_vpn():
	hostname = "10.0.1.1"
	try:
		response = subprocess.check_output(
			['ping', '-c', '3', hostname],
			stderr=subprocess.STDOUT,  # get all output
			universal_newlines=True  # return string not bytes
		)
	except subprocess.CalledProcessError:
		response = None
	return response

try:
	setupLed()
	if check_vpn() is not None:
		config = getConguration()
		djv = Dejavu(config)
		djv.log_event(config['session'], config['vpn_ip'], config['remote_ip'], 'boot')
		atexit.register(exit_handler, djv)
		parser = argparse.ArgumentParser()
		parser.add_argument('-v', '--verbose', action='count', default=0)
		args = parser.parse_args()
		levels = [logging.WARNING, logging.INFO, logging.DEBUG]
		level_index = min(len(levels) - 1, args.verbose)
		level = levels[level_index]  # capped to number of levels
		logging.basicConfig(filename=log, filemode='a', format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
							datefmt='%H:%M:%S', level=level)
		# Get config
		logging.info("Using config '" + config['fingerprint']['name'] + "'")
		djv.log_event(config['session'], config['vpn_ip'], config['remote_ip'],
					  'config: ' + str(config['fingerprint']['name']))

		if __name__ == '__main__':
			a = datetime.now()
			listen = 1
			pause = .5
			it = 1
			try:
				while True:
					song = djv.recognize(MicrophoneRecognizer, seconds=listen)
					if song is None:
						# print str(it) + " - Nothing recognized"
						if args.verbose:
							logging.info(str(it) + ". Nothing recognized")
					else:
						blinkLed()
						djv.log_event(config['session'], config['vpn_ip'], config['remote_ip'], str(song['song_id']))
						print "Recognized %s\n" % (song)
						if args.verbose:
							logging.info(str(it) + ". Recognized from mic with %d seconds: %s\n" % (listen, song))
					it += 1
					time.sleep(pause)
			except KeyboardInterrupt:
				pass
	else:
		print "No vpn connection"

except MySQLdb.Error, e:
	logging.info("Error %d: %s" % (e.args[0], e.args[1]))
	sys.exit(1)
