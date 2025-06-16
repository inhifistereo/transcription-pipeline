#!/bin/bash
# update_env.sh - Helper script to set or update environment variables for the pipeline

# Usage: source ./update_env.sh
# This will prompt for each variable and update your .env file (or create it if missing)

ENV_FILE=".env"

# List of required environment variables
VARS=(
  AZURE_STORAGE_ACCOUNT_NAME
  AZURE_STORAGE_ACCOUNT_KEY
  AZURE_BLOB_VIDEOS_CONTAINER
  AZURE_BLOB_AUDIO_CONTAINER
  AZURE_BLOB_TRANSCRIPTS_CONTAINER
)

echo "Updating environment variables in $ENV_FILE..."

touch "$ENV_FILE"

for VAR in "${VARS[@]}"; do
  # Get current value if exists
  CURRENT=$(grep -E "^$VAR=" "$ENV_FILE" | cut -d'=' -f2-)
  read -p "Enter value for $VAR [${CURRENT}]: " VALUE
  VALUE=${VALUE:-$CURRENT}
  # Remove existing line
  sed -i "/^$VAR=/d" "$ENV_FILE"
  # Add new value
  echo "$VAR=$VALUE" >> "$ENV_FILE"
done

echo "Done. To use these variables, run:"
echo "  export $(grep -v '^#' $ENV_FILE | xargs)"
