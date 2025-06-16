import os
from azure.storage.blob.aio import BlobServiceClient
import logging

async def upload_blob_async(file_path, container, blob_name):
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    async with BlobServiceClient(
        f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=AZURE_STORAGE_ACCOUNT_KEY
    ) as blob_service_client:
        container_client = blob_service_client.get_container_client(container)
        async with container_client:
            with open(file_path, 'rb') as data:
                await container_client.upload_blob(blob_name, data, overwrite=True)
    logging.info(f"Uploaded {blob_name} to {container}")

async def download_blob_async(container, blob_name, file_path):
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    async with BlobServiceClient(
        f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=AZURE_STORAGE_ACCOUNT_KEY
    ) as blob_service_client:
        container_client = blob_service_client.get_container_client(container)
        async with container_client:
            stream = await container_client.download_blob(blob_name)
            with open(file_path, 'wb') as f:
                f.write(await stream.readall())
    logging.info(f"Downloaded {blob_name} from {container}")

async def list_blobs_async(container: str, prefix: str = None):
    """List blobs in a container, optionally filtered by prefix."""
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    async with BlobServiceClient(
        f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=AZURE_STORAGE_ACCOUNT_KEY
    ) as blob_service_client:
        container_client = blob_service_client.get_container_client(container)
        async with container_client:
            blobs = []
            async for blob in container_client.list_blobs(name_starts_with=prefix):
                blobs.append(blob.name)
    return blobs

async def copy_blob_async(source_container, destination_container, blob_name):
    """Copy a blob from one container to another."""
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    async with BlobServiceClient(
        f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=AZURE_STORAGE_ACCOUNT_KEY
    ) as blob_service_client:
        source_blob_url = f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{source_container}/{blob_name}"
        destination_blob_client = blob_service_client.get_blob_client(destination_container, blob_name)
        await destination_blob_client.start_copy_from_url(source_blob_url)
    logging.info(f"Copied {blob_name} from {source_container} to {destination_container}")

async def delete_blob_async(container, blob_name):
    """Delete a blob from a container."""
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    async with BlobServiceClient(
        f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=AZURE_STORAGE_ACCOUNT_KEY
    ) as blob_service_client:
        container_client = blob_service_client.get_container_client(container)
        async with container_client:
            await container_client.delete_blob(blob_name)
    logging.info(f"Deleted {blob_name} from {container}")
