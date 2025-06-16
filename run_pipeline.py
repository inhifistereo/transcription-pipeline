import asyncio
import logging
from utils.azure_blob import list_blobs_async
from download_and_prepare import chunk_and_upload_audio
from transcribe_with_whisper import transcribe_and_upload
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def run_pipeline():
    """
    For each video in the 'videos' container, extract audio, upload to 'audio',
    move processed video to 'videos-processed', and (optionally) transcribe.
    """
    videos_container = os.getenv('AZURE_BLOB_VIDEOS_CONTAINER', 'videos')
    processed_container = os.getenv('AZURE_BLOB_PROCESSED_VIDEOS_CONTAINER')
    if not processed_container:
        raise ValueError("AZURE_BLOB_PROCESSED_VIDEOS_CONTAINER environment variable must be set (e.g., 'videos-processed')")
    audio_container = os.getenv('AZURE_BLOB_AUDIO_CONTAINER', 'audio')
    transcripts_container = os.getenv('AZURE_BLOB_TRANSCRIPTS_CONTAINER', 'transcripts')

    video_blobs = await list_blobs_async(videos_container)
    logging.info("Starting video processing step...")
    if not video_blobs:
        logging.info("No videos found in the container. Proceeding with audio transcription.")
        audio_blobs = await list_blobs_async(audio_container)
        video_ids = set(blob.split('_chunk_')[0] for blob in audio_blobs)
        for video_id in video_ids:
            logging.info(f"Processing transcription for video ID: {video_id}")
            await transcribe_and_upload(video_id)
        return

    for video_blob in video_blobs:
        await chunk_and_upload_audio(
            video_blob_name=video_blob,
            videos_container=videos_container,
            audio_container=audio_container,
            processed_container=processed_container
        )
        video_id = os.path.splitext(os.path.basename(video_blob))[0]
        logging.info(f"Processing video ID: {video_id}")
        await transcribe_and_upload(video_id)
        logging.info(f"Pipeline complete for {video_id}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_pipeline())
