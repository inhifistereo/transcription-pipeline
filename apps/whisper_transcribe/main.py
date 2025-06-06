"""
transcribe_with_whisper.py

This script downloads audio files from Azure Blob Storage, transcribes audio using Whisper, performs speaker diarization using pyannote.audio, aligns speaker segments with transcript segments, and uploads both a merged transcript and a readable speaker script to Azure Blob Storage. It is designed for use in a modular, async pipeline for YouTube playlist transcription and speaker recognition, compatible with Azure Container Apps.

Dependencies:
- whisper
- pyannote.audio
- torch
- ffmpeg-python
- soundfile
- azure-storage-blob
- aiohttp

Purpose:
- To generate a single transcript file per meeting/video, with speaker labels and a human-readable speaker script, using async and temp file best practices.
"""

import asyncio
import logging
from libs.azure_blob import download_blob_async, upload_blob_async
from libs.whisper_wrapper import transcribe_audio
import os
import ffmpeg
import math
import tempfile
import json
from pyannote.audio import Pipeline

def diarize_audio(audio_path):
    from pyannote.audio import Pipeline
    import os
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        raise RuntimeError("HUGGINGFACE_TOKEN environment variable not set. Please set it to your Hugging Face access token.")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=hf_token)
    diarization = pipeline(audio_path)
    segments = []
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": segment.start,
            "end": segment.end,
            "speaker": speaker
        })
    return segments

async def transcribe_and_upload(video_id: str):
    import re
    from libs.azure_blob import list_blobs_async, download_blob_async, upload_blob_async
    from libs.whisper_wrapper import transcribe_audio
    audio_container = os.getenv('AZURE_BLOB_AUDIO_CONTAINER', 'audio')
    chunk_prefix = f"{video_id}_chunk_"
    chunk_blobs = await list_blobs_async(audio_container, prefix=chunk_prefix)
    if not chunk_blobs:
        logging.error(f"No audio chunks found for video_id {video_id} in container {audio_container}")
        return
    temp_files = []
    all_segments = []
    diarization_segments = []
    speaker_script_path = None
    try:
        def chunk_sort_key(x):
            match = re.search(r"chunk_(\\d+)", x)
            return int(match.group(1)) if match else float('inf')
        for chunk_blob in sorted(chunk_blobs, key=chunk_sort_key):
            chunk_path = f"/tmp/{chunk_blob}"
            temp_files.append(chunk_path)
            await download_blob_async(audio_container, chunk_blob, chunk_path)
            transcript = await transcribe_audio(chunk_path)
            result = json.loads(transcript)
            all_segments.extend(result.get('segments', []))
        diarization_audio_path = f"/tmp/{chunk_blobs[0]}"
        diarization_segments = diarize_audio(diarization_audio_path)
        speaker_script_path = f"/tmp/{video_id}_speaker_script.txt"
        with open(speaker_script_path, 'w') as f:
            for seg in all_segments:
                speaker = seg.get('speaker', 'Unknown')
                f.write(f"{speaker} - {seg['start']:.2f} to {seg['end']:.2f}: {seg['text'].strip()}\n\n")
        await upload_blob_async(speaker_script_path, container='transcripts', blob_name=f'{video_id}_speaker_script.txt')
        logging.info(f"Speaker script uploaded for {video_id}")
    finally:
        for path in temp_files + [p for p in [speaker_script_path] if p]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logging.warning(f"Failed to remove temp file {path}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    asyncio.run(transcribe_and_upload(sys.argv[1]))
