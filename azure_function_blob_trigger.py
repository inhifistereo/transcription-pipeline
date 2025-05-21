import os
import logging
import azure.functions as func
from azure.identity import DefaultAzureCredential
import requests

# Environment variables required:
# AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_CONTAINER_APP_NAME, ACA_CONTAINER_IMAGE, ACA_ENVIRONMENT, ACA_RESOURCE_GROUP
# Optionally: ACA_COMMAND (default: python fetch_videos.py --blob <container> <blob_name>)

def main(myblob: func.InputStream):
    logging.info(f"Blob trigger function processed blob: {myblob.name}, Size: {myblob.length} bytes")

    # Get blob info
    container_name = myblob.blob_service.container_name
    blob_name = myblob.name

    # ACA config from environment
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    resource_group = os.environ["AZURE_RESOURCE_GROUP"]
    container_app_name = os.environ["AZURE_CONTAINER_APP_NAME"]
    aca_env = os.environ["ACA_ENVIRONMENT"]
    aca_image = os.environ["ACA_CONTAINER_IMAGE"]
    aca_resource_group = os.environ.get("ACA_RESOURCE_GROUP", resource_group)

    # Prepare command to run in ACA
    command = os.environ.get(
        "ACA_COMMAND",
        f"python fetch_videos.py --blob {container_name} {blob_name}"
    )

    # Authenticate with managed identity
    credential = DefaultAzureCredential()
    token = credential.get_token("https://management.azure.com/.default").token

    # Prepare ACA job payload (using the jobs API)
    job_name = f"yt-job-{blob_name.replace('/', '-')[:40]}"
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{aca_resource_group}/providers/Microsoft.App/jobs/{job_name}?api-version=2023-05-01-preview"
    payload = {
        "location": aca_env,  # This should be the region, e.g., "eastus"
        "properties": {
            "configuration": {
                "replicaTimeout": 36000,  # 10 hours
                "replicaRetryLimit": 1,
                "triggerType": "Manual"
            },
            "template": {
                "containers": [
                    {
                        "image": aca_image,
                        "name": container_app_name,
                        "command": command.split(),
                        "resources": {"cpu": 2, "memory": "4Gi"}
                    }
                ]
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Create or update the job
    resp = requests.put(url, headers=headers, json=payload)
    logging.info(f"ACA job create/update response: {resp.status_code} {resp.text}")

    # Start the job
    start_url = url + "/start"
    start_resp = requests.post(start_url, headers=headers)
    logging.info(f"ACA job start response: {start_resp.status_code} {start_resp.text}")
