import logging
import os
import pickle
from glob import glob

import librosa
import numpy as np
from tqdm import tqdm

from deepspeaker.utils import parallel_function

logger = logging.getLogger(__name__)

SENTENCE_ID = 'sentence_id'
SPEAKER_ID = 'speaker_id'
FILENAME = 'filename'


def find_files(directory, pattern='**/*.wav'):
    """Recursively finds all files matching the pattern."""
    return sorted(glob(directory + pattern, recursive=True))


def read_audio_from_filename(filename, sample_rate):
    audio, _ = librosa.load(filename, sr=sample_rate, mono=True)
    audio = audio.reshape(-1, 1)
    return audio, filename


def trim_silence(audio, threshold):
    """Removes silence at the beginning and end of a sample."""
    energy = librosa.feature.rmse(audio)
    frames = np.nonzero(np.array(energy > threshold))
    indices = librosa.core.frames_to_samples(frames)[1]

    # Note: indices can be an empty array, if the whole audio was silence.
    audio_trim = audio[0:0]
    left_blank = audio[0:0]
    right_blank = audio[0:0]
    if indices.size:
        audio_trim = audio[indices[0]:indices[-1]]
        left_blank = audio[:indices[0]]  # slice before.
        right_blank = audio[indices[-1]:]  # slice after.
    return audio_trim, left_blank, right_blank


def extract_speaker_id(filename):
    return filename.split('/')[-2]


def extract_sentence_id(filename):
    return filename.split('/')[-1].split('_')[1].split('.')[0]


class AudioReader:
    def __init__(self, input_audio_dir=os.getcwd(),
                 output_cache_dir=os.getcwd(),
                 sample_rate=8000,
                 multi_threading=False):
        self.audio_dir = os.path.expanduser(input_audio_dir)
        self.cache_dir = os.path.expanduser(output_cache_dir)
        self.sample_rate = sample_rate
        self.multi_threading = multi_threading
        self.cache_pkl_dir = os.path.join(self.cache_dir, 'audio_cache_pkl')
        self.pkl_filenames = find_files(self.cache_pkl_dir, pattern='/**/*.pkl')
        self.inference_wav_filenames = find_files(os.path.join(os.getcwd(), 'samples'), pattern='/**/*.wav')

        logger.info('audio_dir = {}'.format(self.audio_dir))
        logger.info('cache_dir = {}'.format(self.cache_dir))
        logger.info('sample_rate = {}'.format(sample_rate))

        speakers = set()
        self.speaker_ids_to_filename = {}
        self.speaker_ids_to_filename_wav = {}
        for pkl_filename in self.pkl_filenames:
            speaker_id = os.path.basename(pkl_filename).split('_')[0]
            if speaker_id not in self.speaker_ids_to_filename:
                self.speaker_ids_to_filename[speaker_id] = []
            self.speaker_ids_to_filename[speaker_id].append(pkl_filename)
            speakers.add(speaker_id)
        self.all_speaker_ids = sorted(speakers)

        for file in self.inference_wav_filenames:
            speaker_id = os.path.basename(file).split('_')[0]
            if speaker_id not in self.speaker_ids_to_filename_wav:
                self.speaker_ids_to_filename_wav[speaker_id] = []
            self.speaker_ids_to_filename_wav[speaker_id].append(file)

    def get_enrolled_speakers(self):
        return list(self.speaker_ids_to_filename_wav.keys())

    def load_cache(self, speakers_sub_list=None):
        cache = {}
        metadata = {}

        if speakers_sub_list is None:
            filenames = self.pkl_filenames
        else:
            filenames = []
            for speaker_id in speakers_sub_list:
                filenames.extend(self.speaker_ids_to_filename[speaker_id])

        for pkl_file in filenames:
            with open(pkl_file, 'rb') as f:
                obj = pickle.load(f)
                if FILENAME in obj:
                    cache[obj[FILENAME]] = obj

        for filename in sorted(cache):
            speaker_id = extract_speaker_id(filename)
            if speaker_id not in metadata:
                metadata[speaker_id] = {}
            sentence_id = extract_sentence_id(filename)
            if sentence_id not in metadata[speaker_id]:
                metadata[speaker_id][sentence_id] = []
            metadata[speaker_id][sentence_id] = {SPEAKER_ID: speaker_id,
                                                 SENTENCE_ID: sentence_id,
                                                 FILENAME: filename}

        # metadata # small cache <speaker_id -> sentence_id, filename> - auto generated from self.cache.
        # cache # big cache <filename, data:audio librosa, blanks.>
        return cache, metadata

    def load_audio_file_no_cache(self, speakers_sub_list=None):
        audio = {}

        if speakers_sub_list is None:
            filenames = self.inference_wav_filenames
        else:
            filenames = []
            for speaker_id in speakers_sub_list:
                filenames.extend(self.speaker_ids_to_filename_wav[speaker_id])

        for wav_file in filenames:
            obj = self.get_audio_no_cache(wav_file)
            if FILENAME in obj:
                audio[obj[FILENAME]] = obj

        return audio

    def build_cache(self):
        if not os.path.exists(self.cache_pkl_dir):
            os.makedirs(self.cache_pkl_dir)
        logger.info('Nothing found at {}. Generating all the cache now.'.format(self.cache_pkl_dir))
        logger.info('Looking for the audio dataset in {}.'.format(self.audio_dir))
        audio_files = find_files(self.audio_dir)
        audio_files_count = len(audio_files)
        assert audio_files_count != 0, 'Generate your cache please.'
        logger.info('Found {} files in total in {}.'.format(audio_files_count, self.audio_dir))
        assert len(audio_files) != 0

        if self.multi_threading:
            num_threads = os.cpu_count()
            parallel_function(self.dump_audio_to_pkl_cache, audio_files, num_threads)
        else:
            bar = tqdm(audio_files)
            for filename in bar:
                bar.set_description(filename)
                self.dump_audio_to_pkl_cache(filename)
            bar.close()

    def dump_audio_to_pkl_cache(self, input_filename):
        try:
            cache_filename = input_filename.split('/')[-1].split('.')[0] + '_cache'
            pkl_filename = os.path.join(self.cache_pkl_dir, cache_filename) + '.pkl'

            if os.path.isfile(pkl_filename):
                logger.info('[FILE ALREADY EXISTS] {}'.format(pkl_filename))
                return

            audio, _ = read_audio_from_filename(input_filename, self.sample_rate)
            energy = np.abs(audio[:, 0])
            silence_threshold = np.percentile(energy, 95)
            offsets = np.where(energy > silence_threshold)[0]
            left_blank_duration_ms = (1000.0 * offsets[0]) // self.sample_rate  # frame_id to duration (ms)
            right_blank_duration_ms = (1000.0 * (len(audio) - offsets[-1])) // self.sample_rate
            # _, left_blank, right_blank = trim_silence(audio[:, 0], silence_threshold)
            # logger.info('_' * 100)
            # logger.info('left_blank_duration_ms = {}, right_blank_duration_ms = {}, '
            #             'audio_length = {} frames, silence_threshold = {}'.format(left_blank_duration_ms,
            #                                                                       right_blank_duration_ms,
            #                                                                       len(audio),
            #                                                                       silence_threshold))
            obj = {'audio': audio,
                   'audio_voice_only': audio[offsets[0]:offsets[-1]],
                   'left_blank_duration_ms': left_blank_duration_ms,
                   'right_blank_duration_ms': right_blank_duration_ms,
                   FILENAME: input_filename}

            with open(pkl_filename, 'wb') as f:
                pickle.dump(obj, f)
                logger.info('[DUMP AUDIO] {}'.format(pkl_filename))
        except librosa.util.exceptions.ParameterError as e:
            logger.error(e)
            logger.error('[DUMP AUDIO ERROR SKIPPING FILENAME] {}'.format(input_filename))

    def get_audio_no_cache(self, input_filename):
        try:
            audio, _ = read_audio_from_filename(input_filename, self.sample_rate)
            energy = np.abs(audio[:, 0])
            silence_threshold = np.percentile(energy, 95)
            offsets = np.where(energy > silence_threshold)[0]
            left_blank_duration_ms = (1000.0 * offsets[0]) // self.sample_rate  # frame_id to duration (ms)
            right_blank_duration_ms = (1000.0 * (len(audio) - offsets[-1])) // self.sample_rate

            obj = {'audio': audio,
                   'audio_voice_only': audio[offsets[0]:offsets[-1]],
                   'left_blank_duration_ms': left_blank_duration_ms,
                   'right_blank_duration_ms': right_blank_duration_ms,
                   FILENAME: input_filename}

            return obj
        except librosa.util.exceptions.ParameterError as e:
            logger.error(e)
