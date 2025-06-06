# Moved from utils/azure_blob.py

import os
from azure.storage.blob.aio import BlobServiceClient
import aiohttp

async def download_blob_async(container, blob_name, dest_path):
    account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    blob_service_client = BlobServiceClient(
        f"https://{account_name}.blob.core.windows.net",
        credential=account_key
    )
    blob_client = blob_service_client.get_blob_client(container, blob_name)
    stream = await blob_client.download_blob()
    with open(dest_path, 'wb') as f:
        async for chunk in stream.chunks():
            f.write(chunk)

async def upload_blob_async(src_path, container, blob_name):
    account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    blob_service_client = BlobServiceClient(
        f"https://{account_name}.blob.core.windows.net",
        credential=account_key
    )
    blob_client = blob_service_client.get_blob_client(container, blob_name)
    with open(src_path, 'rb') as data:
        await blob_client.upload_blob(data, overwrite=True)

async def list_blobs_async(container, prefix=None):
    account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    blob_service_client = BlobServiceClient(
        f"https://{account_name}.blob.core.windows.net",
        credential=account_key
    )
    container_client = blob_service_client.get_container_client(container)
    blobs = []
    async for blob in container_client.list_blobs(name_starts_with=prefix):
        blobs.append(blob.name)
    return blobs
