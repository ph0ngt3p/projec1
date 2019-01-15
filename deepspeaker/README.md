# Deep Speaker

### Installation

```
git clone https://github.com/ph0ngt3p/deep-speaker.git && cd deep-speaker

DS_DIR=~/deep-speaker-data
AUDIO_DIR=$DS_DIR/vivos/
CACHE_DIR=$DS_DIR/cache/

mkdir -p $DS_DIR

# will probably work on every python3 impl (e.g. 3.5).
virtualenv -p python3.6 $DS_DIR/venv-speaker
source $DS_DIR/venv-speaker/bin/activate

pip install -r requirements.txt
pip install tensorflow # or tensorflow-gpu if you have a GPU at hand.
```

### Generate audio caches

**Those steps are only required if you want to re-train the model. Instead, if you just want to perform an inference with a pre-trained network, you can skip and go to the generation section.**

The first step generates the cache for the audio files. Caching usually involves sampling the WAV files at 8KHz and trimming the silences.

```
python cli.py --regenerate_full_cache --multi_threading --cache_output_dir $CACHE_DIR --audio_dir $AUDIO_DIR
```

The second step generates the inputs used in the softmax pre-training and the embeddings training. Everything is cached to make the training smoother and faster. In a nutshell, MFCC windows randomly sampled from the audio cached files and put in a unified pickle file.

```
python cli.py --generate_training_inputs --multi_threading --cache_output_dir $CACHE_DIR --audio_dir $AUDIO_DIR
```

### Run softmax pre-training and embeddings training with triplet loss

**Likewise, those steps are only required if you want to re-train the model.**

We perform softmax pre-training to avoid getting stuck in a local minimum. After the softmax pre-training, the speaker classification accuracy should be around 95%.

```
python train_cli.py --loss_on_softmax --data_filename $CACHE_DIR/full_inputs.pkl
```

Next phase is to train the network with the triplet loss.

```
python train_cli.py --loss_on_embeddings --normalize_embeddings --data_filename $CACHE_DIR/full_inputs.pkl
```

Training the embeddings with the triplet loss (specific to deep speaker) takes time and the loss should go around 0.01-0.02 after ~5k steps (on un-normalized embeddings). After only 2k steps, I had 0.04-0.05. I noticed that the softmax pre-training really helped the convergence be faster. The case where (anchor speaker == positive speaker == negative speaker) yields a loss of 0.20. This optimizer gets stuck and cannot do much. This is expected. We can clearly see that the model is learning something. I recall that we train with (anchor speaker == positive speaker != negative speaker).

### Generate embeddings with a pre-trained network

Put audio files into the `samples` directory
```
samples
└── VIVOSDEV01
    ├── VIVOSDEV01_001.wav
    ├── VIVOSDEV01_002.wav
    ├── VIVOSDEV01_003.wav
    ├── VIVOSDEV01_004.wav
```

We can check the SAN and SAP of our new speaker `VIVOSDEV01` by running:

```
python cli.py --unseen_speakers VIVOSDEV01,VIVOSDEV02
python cli.py --unseen_speakers VIVOSDEV01,VIVOSDEV01
```
