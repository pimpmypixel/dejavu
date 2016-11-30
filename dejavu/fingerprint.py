import numpy as np
import os.path
import json
import sys
from datetime import datetime
import logging

log = logging.getLogger(__name__)
# from memory_profiler import profiler
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import (generate_binary_structure,
                                      iterate_structure, binary_erosion)
import hashlib
from operator import itemgetter

IDX_FREQ_I = 0
IDX_TIME_J = 1
PEAK_SORT = True


def fingerprint(channel_samples, config):
    log.debug('fingerprint arr2d start')

    # FFT the signal and extract frequency components
    arr2D = mlab.specgram(
        channel_samples,
        NFFT=config["fingerprint"]["window_size"],
        Fs=config["fingerprint"]["samplerate"],
        window=mlab.window_hanning,
        noverlap=int(config["fingerprint"]["window_size"] * config["fingerprint"]["overlap_ratio"]))[0]
    # print arr2D

    # apply log transform since specgram() returns linear array
    arr2D = 10 * np.log10(arr2D)
    arr2D[arr2D == -np.inf] = 0  # replace infs with zeros

    # find local maxima
    local_maxima = get_2D_peaks(arr2D, config)

    # return hashes
    # print local_maxima
    return generate_hashes(local_maxima, config)


# def get_2D_peaks(arr2D, starttime, plot=True, amp_min=DEFAULT_AMP_MIN):
def get_2D_peaks(arr2D, config):
    log.debug('fingerprint get_2D_peaks')
    # http://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.morphology.iterate_structure.html#scipy.ndimage.morphology.iterate_structure
    struct = generate_binary_structure(2, 1)
    neighborhood = iterate_structure(struct, config["fingerprint"]["neighborhood_size"])

    # find local maxima using our filter shape
    log.debug('fingerprint local maxima start')
    local_max = maximum_filter(arr2D, footprint=neighborhood) == arr2D
    background = (arr2D == 0)

    log.debug('fingerprint binary_erosion start')
    eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)

    # Boolean mask of arr2D with True at peaks
    detected_peaks = local_max - eroded_background

    # extract peaks
    amps = arr2D[detected_peaks]
    j, i = np.where(detected_peaks)

    log.debug('fingerprint filter peaks start')
    # filter peaks
    amps = amps.flatten()
    peaks = zip(i, j, amps)
    peaks_filtered = [x for x in peaks if x[2] > config["fingerprint"]["amp_min"]]  # freq, time, amp

    # get indices for frequency and time
    frequency_idx = [x[1] for x in peaks_filtered]
    time_idx = [x[0] for x in peaks_filtered]

    if config["fingerprint"]["plot"]:
        log.debug('fingerprint plot start')
        # scatter of the peaks
        fig, ax = plt.subplots()
        ax.imshow(arr2D)
        ax.scatter(time_idx, frequency_idx)
        ax.set_xlabel('Time')
        ax.set_ylabel('Frequency')
        ax.set_title("Spectrogram")
        plt.gca().invert_yaxis()
        plt.show()

    return zip(frequency_idx, time_idx)


# @profiler
def generate_hashes(peaks, config):
    """
    Hash list structure:
       sha1_hash[0:20]    time_offset
    [(e05b341a9b77a51fd26, 32), ... ]
    """
    if PEAK_SORT:
        peaks.sort(key=itemgetter(1))

    log.debug('fingerprint generate_hashes start')

    for i in range(len(peaks)):
        for j in range(1, config["fingerprint"]["fan_value"]):
            if (i + j) < len(peaks):

                freq1 = peaks[i][IDX_FREQ_I]
                freq2 = peaks[i + j][IDX_FREQ_I]
                t1 = peaks[i][IDX_TIME_J]
                t2 = peaks[i + j][IDX_TIME_J]
                t_delta = t2 - t1

                if t_delta >= config["fingerprint"]["min_hash"] and t_delta <= config["fingerprint"]["max_hash"]:
                    h = hashlib.sha1(
                        "%s|%s|%s" % (str(freq1), str(freq2), str(t_delta)))
                    yield (h.hexdigest()[0:config["fingerprint"]["fingerprint_redux"]], t1)
