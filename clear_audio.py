import asyncio
import logging
from utils.azure_blob import list_blobs_async, delete_blob_async
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

async def clear_audio_container():
    audio_container = os.getenv("AZURE_BLOB_AUDIO_CONTAINER", "audio")

    # List all blobs in the audio container
    blobs_to_delete = await list_blobs_async(audio_container)

    for blob_name in blobs_to_delete:
        # Delete blob from the audio container
        await delete_blob_async(audio_container, blob_name)
        logging.info(f"Deleted {blob_name} from {audio_container}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(clear_audio_container())
