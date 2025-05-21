import asyncio
import logging
from fetch_videos import fetch_video_ids
from download_and_prepare import process_and_upload
from transcribe_with_whisper import transcribe_and_upload

async def run_pipeline(video_id_or_url: str):
    # If input is a playlist, fetch all video IDs and process each
    if 'playlist' in video_id_or_url:
        ids = await fetch_video_ids(video_id_or_url)
        for video_id in ids:
            await process_and_upload(video_id)
            await transcribe_and_upload(video_id)
            logging.info(f"Pipeline complete for {video_id}")
    else:
        video_id = video_id_or_url.split('v=')[-1] if 'youtube.com' in video_id_or_url else video_id_or_url
        await process_and_upload(video_id)
        await transcribe_and_upload(video_id)
        logging.info(f"Pipeline complete for {video_id}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    asyncio.run(run_pipeline(sys.argv[1]))
