import os
import json

PATH = '/home/tep/deep-speaker-data/vivos'


def create_conf(_path):
    for label in os.listdir(_path):
        p = _path + '/' + label
        if os.path.isdir(p):
            if label == 'train':
                train_set = [l for l in os.listdir(p + '/' + 'waves')]
            else:
                test_set = [l for l in os.listdir(p + '/' + 'waves')]

    with open('./conf.json', 'w') as f:
        dic = {
            'AUDIO': {
                'SAMPLE_RATE': 8000,
                'SPEAKERS_TRAINING_SET': train_set,
                'SPEAKERS_TESTING_SET': test_set
            }
        }
        json.dump(dic, f, indent=4)


if __name__ == '__main__':
    create_conf(PATH)