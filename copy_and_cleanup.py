import asyncio
import logging
import os
from dotenv import load_dotenv
from utils.azure_blob import list_blobs_async, copy_blob_async, delete_blob_async

# Load environment variables from .env file
load_dotenv()

# Pull container names from environment variables
videos_processed_container = os.getenv("AZURE_BLOB_PROCESSED_VIDEOS_CONTAINER", "videos-processed")
videos_container = os.getenv("AZURE_BLOB_VIDEOS_CONTAINER", "videos")

async def copy_and_cleanup():
    # List all blobs in the videos-processed container
    blobs_to_copy = await list_blobs_async(videos_processed_container)

    for blob_name in blobs_to_copy:
        # Copy blob to the videos container
        await copy_blob_async(
            source_container=videos_processed_container,
            destination_container=videos_container,
            blob_name=blob_name
        )
        logging.info(f"Copied {blob_name} from {videos_processed_container} to {videos_container}")

        # Delete blob from the videos-processed container
        await delete_blob_async(videos_processed_container, blob_name)
        logging.info(f"Deleted {blob_name} from {videos_processed_container}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(copy_and_cleanup())
