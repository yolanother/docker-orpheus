# docker-orpheus

## Overview

docker-orpheus is a Dockerized version of Orpheus TTS, an open-source text-to-speech system built on the Llama-3b backbone. Orpheus demonstrates the emergent capabilities of using LLMs for speech synthesis.

[Check out the Orpheus blog post](https://canopylabs.ai/model-releases)

## Abilities

- **Human-Like Speech**: Natural intonation, emotion, and rhythm that is superior to SOTA closed source models
- **Zero-Shot Voice Cloning**: Clone voices without prior fine-tuning
- **Guided Emotion and Intonation**: Control speech and emotion characteristics with simple tags
- **Low Latency**: ~200ms streaming latency for realtime applications, reducible to ~100ms with input streaming

## Running the Docker Container

To run the Docker container, use the following command:

```sh
docker-compose up
```

This will start two services:
1. Web UI: Available at `http://localhost:7325`
2. API: Available at `http://localhost:7324`

## Web UI Usage

The Web UI allows you to perform Voice Cloning and Voice Creation. Voice Cloning supports uploading reference audio or directly recording the audio.

## API Usage

The API provides a streaming text-to-speech endpoint that can be used to generate audio from text in real-time.

### Endpoints

#### GET /api/tts

Converts text to speech and streams the audio as a WAV file.

Parameters:
- `prompt` (required): The text to convert to speech
- `voice` (optional, default: "tara"): The voice to use for speech synthesis. Available voices: "tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"

Example:
```
http://localhost:7324/api/tts?prompt=Hello%20world&voice=tara
```

#### GET /api/voices

Lists all available voices.

Example:
```
http://localhost:7324/api/voices
```

#### GET /api/health

Health check endpoint.

Example:
```
http://localhost:7324/api/health
```

#### API Documentation

The API documentation is available at:
```
http://localhost:7324/api/docs
```

## Prompting

1. The `finetune-prod` models: for the primary model, your text prompt is formatted as `{name}: I went to the ...`. The options for name in order of conversational realism (subjective benchmarks) are "tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe". Our python package does this formatting for you, and the notebook also prepends the appropriate string. You can additionally add the following emotive tags: `<laugh>`, `<chuckle>`, `<sigh>`, `<cough>`, `<sniffle>`, `<groan>`, `<yawn>`, `<gasp>`.

2. The pretrained model: you can either generate speech just conditioned on text, or generate speech conditioned on one or more existing text-speech pairs in the prompt. Since this model hasn't been explicitly trained on the zero-shot voice cloning objective, the more text-speech pairs you pass in the prompt, the more reliably it will generate in the correct voice.

Additionally, use regular LLM generation args like `temperature`, `top_p`, etc. as you expect for a regular LLM. `repetition_penalty>=1.1`is required for stable generations. Increasing `repetition_penalty` and `temperature` makes the model speak faster.

## ⚠️ Usage Disclaimer

This project provides a zero-shot voice cloning TTS model intended for academic research, educational purposes, and legitimate applications, such as personalized speech synthesis, assistive technologies, and linguistic research.

Please note:

- Do not use this model for unauthorized voice cloning, impersonation, fraud, scams, deepfakes, or any illegal activities.
- Ensure compliance with local laws and regulations when using this model and uphold ethical standards.
- The developers assume no liability for any misuse of this model.

We advocate for the responsible development and use of AI and encourage the community to uphold safety and ethical principles in AI research and applications. If you have any concerns regarding ethics or misuse, please contact us.