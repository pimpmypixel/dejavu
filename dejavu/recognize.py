import numpy as np
import pyaudio
import time
from datetime import datetime

import dejavu.fingerprint as fingerprint
import dejavu.decoder as decoder


class BaseRecognizer(object):
    def __init__(self, dejavu):
        self.dejavu = dejavu
        self.Fs = fingerprint.DEFAULT_FS

    def _recognize(self, starttime, *data):
        matches = []
        print str(datetime.now() - starttime) + " - _recognize"
        for d in data:
            matches.extend(self.dejavu.find_matches(d, starttime, Fs=self.Fs))
        return self.dejavu.align_matches(matches, starttime)

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
    default_chunksize = 8096
    default_format = pyaudio.paInt16
    default_channels = 2
    default_samplerate = 44100

    def __init__(self, dejavu):
        super(MicrophoneRecognizer, self).__init__(dejavu)
        self.starttime = datetime.now()
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.data = []
        self.channels = MicrophoneRecognizer.default_channels
        self.chunksize = MicrophoneRecognizer.default_chunksize
        self.samplerate = MicrophoneRecognizer.default_samplerate
        self.recorded = False

    def start_recording(self, channels=default_channels,
                        samplerate=default_samplerate,
                        chunksize=default_chunksize):
        self.chunksize = chunksize
        self.channels = channels
        self.recorded = False
        self.samplerate = samplerate

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        print str(datetime.now() - self.starttime) + " - start recording"
        self.stream = self.audio.open(
            format=self.default_format,
            channels=self.channels,
            rate=self.samplerate,
            input=True,
            frames_per_buffer=self.chunksize,
            # input_device_index=4
        )

        self.data = [[] for i in range(channels)]

    def process_recording(self):
        # print "process recording"
        data = self.stream.read(self.chunksize)
        nums = np.fromstring(data, np.int16)
        for c in range(self.channels):
            self.data[c].extend(nums[c::self.channels])

    def stop_recording(self):
        print str(datetime.now() - self.starttime) + " - stop recording"
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.recorded = True


    """
    def save_recording(self):
        self.audio.terminate()
        print "save recording"
        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename = 'recordings/' + str(timestr) + '.wav'
        print filename
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.default_format))
        wf.setframerate(self.samplerate)
        d = b''.join(self.data)
        wf.writeframes(d)
        wf.close()
        print "write"
    """

    def recognize_recording(self):
        print str(datetime.now() - self.starttime) + " - recognize recording"
        if not self.recorded:
            raise NoRecordingError("Recording was not complete/begun")
        return self._recognize(self.starttime, *self.data)

    def get_recorded_time(self):
        return len(self.data[0]) / self.rate

    def recognize(self, seconds=2):
        self.start_recording()
        for i in range(0, int(self.samplerate / self.chunksize
                * seconds)):
            self.process_recording()
        self.stop_recording()
        return self.recognize_recording()


class NoRecordingError(Exception):
    pass
