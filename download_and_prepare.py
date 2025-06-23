import asyncio
import logging
from utils.azure_blob import download_blob_async, upload_blob_async
from utils.ffmpeg_tools import extract_audio_to_wav
import os
import math
import tempfile
import ffmpeg

async def chunk_and_upload_audio(video_blob_name: str, videos_container: str = 'videos', audio_container: str = 'audio', processed_container: str = 'videos-processed', chunk_length_sec: int = 1800):
    """
    Download video from blob, split audio into 30-min chunks, upload each chunk to audio container, move video to processed container.
    """
    video_id = os.path.splitext(os.path.basename(video_blob_name))[0]
    # Download video to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_video:
        tmp_video_path = tmp_video.name
    await download_blob_async(videos_container, video_blob_name, tmp_video_path)
    # Extract full audio to temp wav
    full_wav_path = f'{video_id}_full.wav'
    await extract_audio_to_wav(tmp_video_path, full_wav_path)
    # Upload full wav for diarization
    await upload_blob_async(full_wav_path, container=audio_container, blob_name=full_wav_path)
    logging.info(f"Uploaded full audio {full_wav_path} to {audio_container}")
    # Get total duration using ffmpeg probe
    probe = ffmpeg.probe(full_wav_path)
    total_sec = float(probe['format']['duration'])
    num_chunks = math.ceil(total_sec / chunk_length_sec)
    chunk_paths = []
    for i in range(num_chunks):
        start = i * chunk_length_sec
        duration = min(chunk_length_sec, total_sec - start)
        chunk_file = f'{video_id}_chunk_{i+1}.wav'
        (
            ffmpeg
            .input(full_wav_path, ss=start, t=duration)
            .output(chunk_file, acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(quiet=True)
        )
        await upload_blob_async(chunk_file, container=audio_container, blob_name=chunk_file)
        logging.info(f"Uploaded audio chunk {chunk_file} to {audio_container}")
        chunk_paths.append(chunk_file)
    # Move video to processed container
    from azure.storage.blob.aio import BlobServiceClient
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    blob_service_client = BlobServiceClient(
        f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=AZURE_STORAGE_ACCOUNT_KEY
    )
    src_client = blob_service_client.get_blob_client(videos_container, video_blob_name)
    dest_client = blob_service_client.get_blob_client(processed_container, video_blob_name)
    src_url = src_client.url
    await dest_client.start_copy_from_url(src_url)
    await src_client.delete_blob()
    logging.info(f"Moved {video_blob_name} to {processed_container}")
    # Clean up
    for f in [tmp_video_path, full_wav_path] + chunk_paths:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    asyncio.run(chunk_and_upload_audio(sys.argv[1]))
