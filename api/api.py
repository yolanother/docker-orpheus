import struct
import logging
from typing import Iterator, Dict
import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from orpheus_tts import OrpheusModel
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Orpheus TTS API",
    description="API for Orpheus Text-to-Speech",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc"
)

# Initialize the Orpheus TTS models
models: Dict[str, OrpheusModel] = {}

def load_model(model_id: str, model_path: str = None):
    """Load an Orpheus TTS model."""
    try:
        if model_id == "finetune-prod":
            model_name = model_path if model_path else "/Orpheus-TTS/models/canopylabs/orpheus-tts-0.1-finetune-prod"
            logger.info(f"Loading finetuned model from: {model_name}")
            models[model_id] = OrpheusModel(model_name=model_name)
            return True
        elif model_id == "pretrained":
            model_name = model_path if model_path else "/Orpheus-TTS/models/canopylabs/orpheus-3b-0.1-pretrained"
            logger.info(f"Loading pretrained model from: {model_name}")
            models[model_id] = OrpheusModel(model_name=model_name)
            return True
        else:
            logger.error(f"Unknown model ID: {model_id}")
            return False
    except Exception as e:
        logger.error(f"Error loading model {model_id}: {str(e)}")
        return False

# Load models on startup
@app.on_event("startup")
async def startup_event():
    """Load models on startup."""
    logger.info("Loading models...")
    load_model("finetune-prod")
    load_model("pretrained")
    logger.info(f"Loaded {len(models)} models")

def create_wav_header(sample_rate=24000, bits_per_sample=16, channels=1):
    """Create a WAV header for the audio stream."""
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8

    data_size = 0

    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,       
        b'WAVE',
        b'fmt ',
        16,                  
        1,             
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        data_size
    )
    return header

def generate_audio_stream(prompt: str, voice: str = "tara", model: str = "finetune-prod") -> Iterator[bytes]:
    """Generate audio stream from text prompt."""
    # First yield the WAV header
    yield create_wav_header()

    # Get the appropriate model
    if model not in models:
        # Try to load the model if it's not loaded
        if not load_model(model):
            logger.error(f"Model {model} not available, falling back to finetune-prod")
            model = "finetune-prod"
            # If finetune-prod is also not available, raise an exception
            if model not in models:
                if not load_model("finetune-prod"):
                    raise HTTPException(status_code=500, detail="No models available")
    
    engine = models[model]

    # Generate speech and stream the audio chunks
    try:
        syn_tokens = engine.generate_speech(
            prompt=prompt,
            voice=voice,
            repetition_penalty=1.1,
            stop_token_ids=[128258],
            max_tokens=2000,
            temperature=0.4,
            top_p=0.9
        )
        
        for chunk in syn_tokens:
            yield chunk
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.get("/api/tts", response_class=StreamingResponse)
async def tts(
    prompt: str = Query(..., description="Text to convert to speech"),
    voice: str = Query("tara", description="Voice to use for speech synthesis"),
    model: str = Query("finetune-prod", description="Model to use (finetune-prod or pretrained)")
):
    """
    Convert text to speech and stream the audio as a WAV file.
    
    - **prompt**: The text to convert to speech
    - **voice**: The voice to use (default: tara)
    - **model**: The model to use (default: finetune-prod)
    """
    return StreamingResponse(
        generate_audio_stream(prompt, voice, model),
        media_type="audio/wav"
    )

@app.get("/api/voices")
async def list_voices():
    """List all available voices."""
    # This is a placeholder - you may need to adjust based on actual available voices
    return {
        "voices": [
            {"id": "tara", "name": "Tara", "description": "Default female voice"},
            {"id": "leah", "name": "Leah", "description": "Female voice"},
            {"id": "jess", "name": "Jess", "description": "Female voice"},
            {"id": "leo", "name": "Leo", "description": "Male voice"},
            {"id": "dan", "name": "Dan", "description": "Male voice"},
            {"id": "mia", "name": "Mia", "description": "Female voice"},
            {"id": "zac", "name": "Zac", "description": "Male voice"},
            {"id": "zoe", "name": "Zoe", "description": "Female voice"}
        ]
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    loaded_models = {model_id: "loaded" for model_id in models.keys()}
    return {
        "status": "ok",
        "models": {
            "finetune-prod": loaded_models.get("finetune-prod", "not loaded"),
            "pretrained": loaded_models.get("pretrained", "not loaded")
        }
    }

@app.get("/api/models")
async def list_models():
    """List all available models."""
    return {
        "models": [
            {
                "id": "finetune-prod",
                "name": "Finetuned Production",
                "description": "A finetuned model for everyday TTS applications",
                "status": "loaded" if "finetune-prod" in models else "not loaded"
            },
            {
                "id": "pretrained",
                "name": "Pretrained",
                "description": "Base model trained on 100k+ hours of English speech data",
                "status": "loaded" if "pretrained" in models else "not loaded"
            }
        ]
    }

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 7324))
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)