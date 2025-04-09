#!/bin/bash
set -e

# Set up logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check if HUGGINGFACE_TOKEN is set
if [ -z "$HUGGINGFACE_TOKEN" ]; then
    log "Error: HUGGINGFACE_TOKEN environment variable is not set"
    exit 1
fi

# Login to Hugging Face
log "Logging in to Hugging Face with token"
huggingface-cli login --token $HUGGINGFACE_TOKEN

# Define models to download
MODELS=(
    "canopylabs/orpheus-tts-0.1-finetune-prod"
    "canopylabs/orpheus-3b-0.1-pretrained"
    "canopylabs/3b-de-pretrain-research_release"
)

# Base directory for models
BASE_DIR="/Orpheus-TTS/models"

# Download each model
for MODEL in "${MODELS[@]}"; do
    MODEL_DIR="$BASE_DIR/$MODEL"
    log "Creating directory: $MODEL_DIR"
    mkdir -p "$MODEL_DIR"
    
    log "Downloading model: $MODEL"
    huggingface-cli download "$MODEL" --local-dir "$MODEL_DIR"
    
    if [ $? -eq 0 ]; then
        log "Successfully downloaded model: $MODEL"
    else
        log "Failed to download model: $MODEL"
        exit 1
    fi
done

log "All models downloaded successfully"
