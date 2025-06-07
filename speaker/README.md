# Speaker Identification (Python 3.8, pyannote.audio)

This module identifies speakers in diarized audio segments using known voice embeddings.

## Requirements
- Python 3.8
- pyannote.audio==2.1.1
- torch

## Usage

Build the Docker image:
```bash
docker build -t speaker-id .
```

Run the app (example):
```bash
docker run --rm -v $(pwd):/app speaker-id \
  audio.wav diarization.json embeddings.pt output.json
```

## Arguments
- `audio.wav`: Path to the full audio file
- `diarization.json`: Diarization output (segments)
- `embeddings.pt`: Known speaker embeddings (PyTorch file)
- `output.json`: Output file with labeled segments

## Notes
- This app is designed to be run as a step in a modular pipeline.
- All heavy dependencies are isolated to this container.
