import struct
from typing import Iterator
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from orpheus_speech import OrpheusModel
import os

app = FastAPI(
    title="Orpheus TTS API",
    description="API for Orpheus Text-to-Speech",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc"
)

# Initialize the Orpheus TTS model
engine = OrpheusModel(model_name="canopyai/orpheus-tts-0.1-finetune-prod")

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

def generate_audio_stream(prompt: str, voice: str = "tara") -> Iterator[bytes]:
    """Generate audio stream from text prompt."""
    # First yield the WAV header
    yield create_wav_header()

    # Generate speech and stream the audio chunks
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

@app.get("/api/tts", response_class=StreamingResponse)
async def tts(
    prompt: str = Query(..., description="Text to convert to speech"),
    voice: str = Query("tara", description="Voice to use for speech synthesis")
):
    """
    Convert text to speech and stream the audio as a WAV file.
    
    - **prompt**: The text to convert to speech
    - **voice**: The voice to use (default: tara)
    """
    return StreamingResponse(
        generate_audio_stream(prompt, voice),
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
    return {"status": "ok", "model": "canopyai/orpheus-tts-0.1-finetune-prod"}

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 7324))
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)