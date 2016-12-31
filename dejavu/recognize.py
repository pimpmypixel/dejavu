import numpy as np
import pyaudio
import time
import sys
import logging
import pprint
# from memory_profiler import profile
from datetime import datetime

# import dejavu.fingerprint as fingerprint
import dejavu.decoder as decoder


class BaseRecognizer(object):
	def __init__(self, dejavu):
		self.dejavu = dejavu

	def _recognize(self, *data):
		matches = []
		for d in data:
			matches.extend(
				self.dejavu.find_matches(d))
		return self.dejavu.align_matches(matches)

	def recognize(self):
		pass  # base class does nothing


class MicrophoneRecognizer(BaseRecognizer):
	# hardware dependent
	default_format = pyaudio.paInt16

	def __init__(self, dejavu):
		self.config = vars(dejavu)
		super(MicrophoneRecognizer, self).__init__(dejavu)
		self.starttime = datetime.now()
		self.audio = pyaudio.PyAudio()
		self.stream = None
		self.data = []
		self.recorded = False

	def start_recording(self):
		self.recorded = False
		if self.stream:
			self.stream.stop_stream()
			self.stream.close()
		self.stream = self.audio.open(
			format=self.default_format,
			channels=self.config['config']['soundcard']['channels'],
			rate=self.config['config']['fingerprint']['samplerate'],
			input=True,
			frames_per_buffer=self.config['config']['soundcard']['chunksize'],
			input_device_index=1
		)
		self.data = [[] for i in range(self.config['config']['soundcard']['channels'])]

	def process_recording(self):
		data = self.stream.read(self.config['config']['soundcard']['chunksize'])
		nums = np.fromstring(data, np.int16)
		for c in range(self.config['config']['soundcard']['channels']):
			self.data[c].extend(nums[c::self.config['config']['soundcard']['chunksize']])
		#try:
		#	data = self.stream.read(self.config['config']['soundcard']['chunksize'])
		#	nums = np.fromstring(data, np.int16)
		#	for c in range(self.config['config']['soundcard']['channels']):
		#		self.data[c].extend(nums[c::self.config['config']['soundcard']['chunksize']])
		#except IOError as ex:
		#	if ex[1] != pyaudio.paInputOverflowed:
		#        	raise
		#    	data = '\x00' * self.config['config']['soundcard']['chunksize']

	def stop_recording(self):
		self.stream.stop_stream()
		self.stream.close()
		self.stream = None
		self.recorded = True

	def recognize_recording(self):
		if not self.recorded:
			raise NoRecordingError("Recording was not complete/begun")
		return self._recognize(*self.data)

	def get_recorded_time(self):
		return len(self.data[0]) / self.config['config']['fingerprint']['samplerate']

	def recognize(self, seconds=2):
		self.start_recording()
		for i in range(0, int(self.config['config']['fingerprint']['samplerate'] / self.config['config']['soundcard'][
			'chunksize'] * seconds)):
			self.process_recording()
		self.stop_recording()
		#print self.get_recorded_time()
		return self.recognize_recording()


class NoRecordingError(Exception):
	pass
