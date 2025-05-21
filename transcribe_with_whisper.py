import asyncio
import logging
from utils.azure_blob import download_blob_async, upload_blob_async
from utils.whisper_wrapper import transcribe_audio
import os
import ffmpeg
import math
import tempfile
import json

async def split_audio_to_chunks(audio_path: str, chunk_length_sec: int = 1800) -> list:
    """Split audio into chunks of chunk_length_sec seconds. Returns list of chunk file paths."""
    import soundfile as sf
    data, samplerate = sf.read(audio_path)
    total_sec = len(data) / samplerate
    num_chunks = math.ceil(total_sec / chunk_length_sec)
    chunk_paths = []
    for i in range(num_chunks):
        start = i * chunk_length_sec
        end = min((i + 1) * chunk_length_sec, total_sec)
        chunk_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        (
            ffmpeg
            .input(audio_path, ss=start, t=(end - start))
            .output(chunk_file, acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(quiet=True)
        )
        chunk_paths.append(chunk_file)
    return chunk_paths

async def transcribe_and_upload(video_id: str):
    audio_blob = f"{video_id}.wav"
    transcript_blob = f"{video_id}.json"
    audio_path = f"/tmp/{audio_blob}"
    transcript_path = f"/tmp/{transcript_blob}"
    # Download audio from Azure Blob
    await download_blob_async(container='audio', blob_name=audio_blob, file_path=audio_path)
    # Split audio into 30 min chunks
    chunk_paths = await split_audio_to_chunks(audio_path, chunk_length_sec=1800)
    # Transcribe each chunk and merge results
    all_segments = []
    for chunk_path in chunk_paths:
        transcript = await transcribe_audio(chunk_path)
        result = json.loads(transcript)
        all_segments.extend(result.get('segments', []))
        os.remove(chunk_path)
    # Save merged transcript as JSON
    merged = {"segments": all_segments}
    with open(transcript_path, 'w') as f:
        json.dump(merged, f, indent=2)
    # Upload transcript
    await upload_blob_async(transcript_path, container='transcripts', blob_name=transcript_blob)
    logging.info(f"Transcript uploaded for {video_id}")
    # Clean up
    os.remove(audio_path)
    os.remove(transcript_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    asyncio.run(transcribe_and_upload(sys.argv[1]))
