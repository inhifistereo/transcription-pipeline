import os
from azure.storage.blob.aio import BlobServiceClient
import logging

AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')

blob_service_client = BlobServiceClient(
    f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=AZURE_STORAGE_ACCOUNT_KEY
)

async def upload_blob_async(file_path, container, blob_name):
    container_client = blob_service_client.get_container_client(container)
    async with container_client:
        with open(file_path, 'rb') as data:
            await container_client.upload_blob(blob_name, data, overwrite=True)
    logging.info(f"Uploaded {blob_name} to {container}")

async def download_blob_async(container, blob_name, file_path):
    container_client = blob_service_client.get_container_client(container)
    async with container_client:
        stream = await container_client.download_blob(blob_name)
        with open(file_path, 'wb') as f:
            f.write(await stream.readall())
    logging.info(f"Downloaded {blob_name} from {container}")
