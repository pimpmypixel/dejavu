import numpy as np
import pyaudio
import time
import sys
import logging

log = logging.getLogger(__name__)
# from memory_profiler import profile
from datetime import datetime

# import dejavu.fingerprint as fingerprint
import dejavu.decoder as decoder


class BaseRecognizer(object):
	def __init__(self, dejavu):
		self.dejavu = dejavu

	def _recognize(self, *data):
		matches = []
		log.debug('_recognize')
		for d in data:
			matches.extend(
				self.dejavu.find_matches(d))
		return self.dejavu.align_matches(matches)

	def recognize(self):
		pass  # base class does nothing


class MicrophoneRecognizer(BaseRecognizer):
	# hardware dependent
	default_chunksize = 8096
	default_format = pyaudio.paInt16
	default_channels = 1
	default_samplerate = 44100

	def __init__(self, dejavu):
		#print vars(dejavu)
		log.debug('__init__ MicrophoneRecognizer')
		super(MicrophoneRecognizer, self).__init__(dejavu)
		self.starttime = datetime.now()
		self.audio = pyaudio.PyAudio()
		self.stream = None
		self.data = []
		self.channels = MicrophoneRecognizer.default_channels
		self.chunksize = MicrophoneRecognizer.default_chunksize
		self.samplerate = MicrophoneRecognizer.default_samplerate
		self.recorded = False

	def start_recording(self,
						channels=default_channels,
						samplerate=default_samplerate,
						chunksize=default_chunksize
						):
		self.chunksize = chunksize
		self.channels = channels
		self.recorded = False
		self.samplerate = samplerate

		if self.stream:
			self.stream.stop_stream()
			self.stream.close()

		log.debug('start_recording')
		self.stream = self.audio.open(
			format=self.default_format,
			channels=self.channels,
			rate=self.samplerate,
			input=True,
			frames_per_buffer=self.chunksize,
			input_device_index=1
		)
		self.data = [[] for i in range(channels)]

	def process_recording(self):
		data = self.stream.read(self.chunksize)
		nums = np.fromstring(data, np.int16)
		for c in range(self.channels):
			self.data[c].extend(nums[c::self.channels])

	def stop_recording(self):
		log.debug('stop_recording')
		self.stream.stop_stream()
		self.stream.close()
		self.stream = None
		self.recorded = True

	def recognize_recording(self):
		log.debug('recognize_recording')
		if not self.recorded:
			raise NoRecordingError("Recording was not complete/begun")
		return self._recognize(*self.data)

	def get_recorded_time(self):
		log.debug('get_recorded_time')
		return len(self.data[0]) / self.rate

	def recognize(self, seconds=2):
		log.debug('recognize')
		self.start_recording()
		for i in range(0, int(self.samplerate / self.chunksize
									  * seconds)):
			self.process_recording()
		self.stop_recording()
		return self.recognize_recording()


class NoRecordingError(Exception):
	pass
