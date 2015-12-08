import time
import os.path
import numpy as np
import pyaudio
import json

import dejavu.decoder as decoder


with open(os.path.dirname(__file__) + '/../bassment.cnf') as f:
    config = json.load(f)


class BaseRecognizer(object):
    def __init__(self, dejavu):
        self.dejavu = dejavu
        self.Fs = config["fingerprint"]["fs"]

    def _recognize(self, *data):
        print "_recognize"
        matches = []
        for d in data:
            matches.extend(self.dejavu.find_matches(d, Fs=self.Fs))
        return self.dejavu.align_matches(matches)

    def recognize(self):
        pass  # base class does nothing


class FileRecognizer(BaseRecognizer):
    def __init__(self, dejavu):
        super(FileRecognizer, self).__init__(dejavu)

    def recognize_file(self, filename):
        frames, self.Fs, file_hash = decoder.read(filename, self.dejavu.limit)

        t = time.time()
        match = self._recognize(*frames)
        t = time.time() - t

        if match:
            match['match_time'] = t

        return match

    def recognize(self, filename):
        return self.recognize_file(filename)


class MicrophoneRecognizer(BaseRecognizer):
    print "mic recognize"
    default_format = pyaudio.paInt16

    def __init__(self, dejavu):
        super(MicrophoneRecognizer, self).__init__(dejavu)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.data = []
        self.recorded = False

    def start_recording(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        print "start rec"

        self.stream = self.audio.open(
            input=True,
            format=self.default_format,
            channels=config["recognize"]["channels"],
            rate=config["recognize"]["samplerate"],
            frames_per_buffer=config["recognize"]["chunksize"],
            input_device_index=config["recognize"]["device"]
        )

        self.data = [[] for i in range(config["recognize"]["channels"])]

    def process_recording(self):
        print "process_recording"
        data = self.stream.read(config["recognize"]["chunksize"])
        nums = np.fromstring(data, np.int16)
        for c in range(config["recognize"]["channels"]):
            self.data[c].extend(nums[c::config["recognize"]["channels"]])

    def stop_recording(self):
        print "stop_recording"
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.recorded = True

    def recognize_recording(self):
        print "recognize_recording"
        if not self.recorded:
            raise NoRecordingError("Recording was not complete/begun")
        return self._recognize(*self.data)

    def get_recorded_time(self):
        print "get_recorded_time"
        return len(self.data[0]) / self.rate

    def recognize(self, seconds=10):
        print "recognize"
        self.start_recording()
        for i in range(0, int(config["recognize"]["samplerate"] / config["recognize"]["chunksize"] * seconds)):
            self.process_recording()
        self.stop_recording()
        return self.recognize_recording()


class NoRecordingError(Exception):
    pass
