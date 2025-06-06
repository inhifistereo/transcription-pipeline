import os
from shared.utils.blob import download_blob, upload_blob
from shared.utils.logging import setup_logging
from pyannote.audio import Pipeline

def diarize(audio_path, output_path):
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=os.environ['HUGGINGFACE_TOKEN'])
    diarization = pipeline(audio_path)
    # Save diarization output to output_path

def main():
    setup_logging()
    # Download audio, run diarization, upload result

if __name__ == '__main__':
    main()
