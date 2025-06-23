import sys
from pathlib import Path

# Ensure project root is in sys.path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

import asyncio
import logging
from utils.azure_blob import list_blobs_async, delete_blob_async
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

async def clear_transcripts_container():
    transcripts_container = os.getenv("AZURE_BLOB_TRANSCRIPTS_CONTAINER", "transcripts")

    # List all blobs in the transcripts container
    blobs_to_delete = await list_blobs_async(transcripts_container)

    for blob_name in blobs_to_delete:
        # Delete blob from the transcripts container
        await delete_blob_async(transcripts_container, blob_name)
        logging.info(f"Deleted {blob_name} from {transcripts_container}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(clear_transcripts_container())
