import multiprocessing
import os
import traceback
import sys
from datetime import datetime
import logging

log = logging.getLogger(__name__)

from dejavu.database import get_database, Database
import dejavu.decoder as decoder
import fingerprint


class Dejavu(object):
	SONG_ID = "song_id"
	SONG_NAME = 'song_name'
	CONFIDENCE = 'confidence'
	MATCH_TIME = 'match_time'
	OFFSET = 'offset'
	OFFSET_SECS = 'offset_seconds'

	def __init__(self, config):
		log.debug('__init__ Dejavu')
		super(Dejavu, self).__init__()
		self.config = config
		# initialize db
		db_cls = get_database(config.get("database_type", None))
		self.db = db_cls(**config.get("database", {}))
		self.db.setup()

	def get_fingerprinted_songs(self):
		# if we should limit seconds fingerprinted,
		# None|-1 means use entire track
		self.limit = self.config.get("fingerprint_limit", None)
		if self.limit == -1:  # for JSON compatibility
			self.limit = None
		self.get_fingerprinted_songs()

		# get songs previously indexed
		self.songs = self.db.get_songs()
		self.songhashes_set = set()  # to know which ones we've computed before
		for song in self.songs:
			song_hash = song[Database.FIELD_FILE_SHA1]
			self.songhashes_set.add(song_hash)

	def find_matches(self, samples):
		log.debug('find_matches')
		hashes = fingerprint.fingerprint(samples, self.config)
		return self.db.return_matches(hashes)

	def align_matches(self, matches):
		"""
			Finds hash matches that align in time with other matches and finds
			consensus about which hashes are "true" signal from the audio.
			Returns a dictionary with match information.
		"""
		# align by diffs
		log.debug('align_matches')
		diff_counter = {}
		largest = 0
		largest_count = 0
		song_id = -1
		for tup in matches:
			sid, diff = tup
			if diff not in diff_counter:
				diff_counter[diff] = {}
			if sid not in diff_counter[diff]:
				diff_counter[diff][sid] = 0
			diff_counter[diff][sid] += 1

			if diff_counter[diff][sid] > largest_count:
				largest = diff
				largest_count = diff_counter[diff][sid]
				song_id = sid

		song = self.db.get_song_by_id(song_id)
		if song:
			songname = song.get(Dejavu.SONG_NAME, None)
		else:
			return None

		# return match info
		nseconds = round(float(largest) / self.config.get('fingerprint').get('samplerate') *
						 self.config.get('fingerprint').get('window_size') *
						 self.config.get('fingerprint').get('overlap_ratio'), 5)
		song = {
			Dejavu.SONG_ID: song_id,
			Dejavu.SONG_NAME: songname,
			Dejavu.CONFIDENCE: largest_count,
			Dejavu.OFFSET: int(largest),
			Dejavu.OFFSET_SECS: nseconds,
			Database.FIELD_FILE_SHA1: song.get(Database.FIELD_FILE_SHA1, None), }
		return song

	def recognize(self, recognizer, *options, **kwoptions):
		log.debug('recognize')
		r = recognizer(self)
		return r.recognize(*options, **kwoptions)

	def log_event(self, session, ip, remote, message):
		self.db.log_event(session, ip, remote, message)


def chunkify(lst, n):
	"""
	Splits a list into roughly n equal parts.
	http://stackoverflow.com/questions/2130016/splitting-a-list-of-arbitrary-size-into-only-roughly-n-equal-parts
	"""
	return [lst[i::n] for i in xrange(n)]
