#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
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
import shortuuid
import ipgetter
import subprocess
from urlparse import urlparse, parse_qs

PORT_NUMBER = 8000
config = {}
warnings.filterwarnings("ignore")
shouldrun = False
redled = "XIO-P0"

def getConguration():
	db = os.path.dirname(__file__) + "/conf/database.json"
	global pause
	pause = .5
	global listen
	listen = 1
	with open(db) as f:
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
				cur = con.cursor()
				cur.execute(
					"SELECT * FROM `configurations` WHERE id = (SELECT active FROM `states` ORDER BY id DESC limit 1)")
				config['fingerprint'] = cur.fetchone()
				config['session'] = shortuuid.uuid()
				config['remote_ip'] = ipgetter.myip()
				config['vpn_ip'] = ni.ifaddresses('tun0')[2][0]['addr']
				print config
				config['fingerprint']['amp_min'] = 10
				config['fingerprint']['plot'] = 0
				config['verbose'] = False
				config['soundcard'] = {
					"chunksize": 8096,
					"channels": 1
				}
				return config
			else:
				print "Connection unsuccessful"
		except MySQLdb.Error, e:
			print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
			print "MySQL Error: %s" % str(e)

def blinkLed(blinks):
	#GPIO.setup(redled, GPIO.OUT)
	#for j in range(1, blinks):
	#	GPIO.output(redled, GPIO.LOW)
	#	time.sleep(0.05)
	#	GPIO.output(redled, GPIO.HIGH)
	#	time.sleep(0.05)
	#GPIO.cleanup()
	return

def exit_handler(djv):
	blinkLed(4)
	djv.log_event('action', 'end')

def check_vpn():
	return True
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

class webHandler(BaseHTTPRequestHandler, Dejavu):
	def do_GET(self):
		global pause
		url = "http://"+str(config['vpn_ip'])+":"+str(PORT_NUMBER)
		p = self.path
		v = urlparse(p).query
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
        	#self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
		djv.log_event('agent', str(self.headers['user-agent']))
		if v == 'on':
			djv.log_event('listen', 'on')
			print "listen"
			blinkLed(5)
			self.wfile.write("<h2>Now listening<br><a href='"+url+"?off'>off</a></h2>")
			global shouldrun
			shouldrun = True
		elif v == 'off':
			djv.log_event('listen', 'off')
			print "off"
			blinkLed(5)
			self.wfile.write("<h2>Stopped listening<br><a href='"+url+"?on'>on</a></h2>")
			shouldrun = False
		elif v == 'restart':
			djv.log_event('action', 'restart')
			print "restart"
			blinkLed(10)
			self.wfile.write("<h2>Restarting</h2>")
			os.system('reboot')
		elif v.startswith("pause="):
			v = v.replace("pause=", "")
			v = float(v)
			if isinstance(v, float):
				global pause
				pause = float(v)
				djv.log_event('pause', pause)
		elif v.startswith("listen="):
			v = v.replace("listen=", "")
			v = float(v)
			if isinstance(v, float):
				global listen
				listen = float(v)
				djv.log_event('listen', listen)
		else:
			self.wfile.write("welcome")
		return
	def log_message(self, format, *args):
		return

server = HTTPServer(('', PORT_NUMBER), webHandler)
thread = threading.Thread(target = server.serve_forever)
thread.daemon = True

try:
	thread.start()
except KeyboardInterrupt:
    server.shutdown()
    sys.exit(0)

try:
	if check_vpn() is not None:
		try:
			config = getConguration()
			djv = Dejavu(config)
			djv.create_session(config['fingerprint']['id'], config['vpn_ip'], config['remote_ip'])
			print 'Session '+str(config['session'])
			djv.log_event('action', 'boot')
			atexit.register(exit_handler, djv)
			print 'Start listening: http://'+str(config['vpn_ip'])+':'+str(PORT_NUMBER)+'/?on'
			print 'Stop listening: http://'+str(config['vpn_ip'])+':'+str(PORT_NUMBER)+'/?off'
			if __name__ == '__main__':
				a = datetime.now()
				listen = 1
				it = 1
				try:
					while True:
						#print listen,pause
						if(shouldrun):
							blinkLed(2)
							song = djv.recognize(MicrophoneRecognizer, seconds=listen)
							if song is not None:
								djv.log_event('match', str(song['song_id']))
								print "Recognized %s\n" % (song)
								blinkLed(5)
						it += 1
						time.sleep(pause)
				except KeyboardInterrupt:
					pass
	        except KeyError:
	            print "No config"
except KeyboardInterrupt:
	#djv.log_event('mysql_error', str(e.args[1]))
	server.socket.close()
	sys.exit(1)
