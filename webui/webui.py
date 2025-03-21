import gradio as gr
import requests
import tempfile
import os
import argparse
import io
from pydub import AudioSegment
import numpy as np

# Parse command line arguments
parser = argparse.ArgumentParser(description="Orpheus TTS Web UI")
parser.add_argument("--server_port", type=int, default=7325, help="Port to run the Gradio server on")
parser.add_argument("--device", type=str, default="0", help="Device to run the model on")
args = parser.parse_args()

# API endpoint
API_BASE_URL = "http://localhost:7324/api"

def get_available_voices():
    """Get the list of available voices from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/voices")
        if response.status_code == 200:
            voices = response.json().get("voices", [])
            return [voice["id"] for voice in voices]
        else:
            print(f"Error fetching voices: {response.status_code}")
            return ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"]
    except Exception as e:
        print(f"Exception fetching voices: {e}")
        return ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"]

def text_to_speech(text, voice, model="finetune-prod", temperature=0.4, repetition_penalty=1.1):
    """Convert text to speech using the API."""
    if not text:
        return None, "Please enter some text to convert to speech."
    
    try:
        # Check if the model is available
        model_response = requests.get(f"{API_BASE_URL}/models")
        if model_response.status_code == 200:
            models_data = model_response.json().get("models", [])
            available_models = [m for m in models_data if m.get("status") == "loaded"]
            available_model_ids = [m.get("id") for m in available_models]
            
            if model not in available_model_ids:
                if "finetune-prod" in available_model_ids:
                    model = "finetune-prod"
                    print(f"Model {model} not available, falling back to finetune-prod")
                elif len(available_model_ids) > 0:
                    model = available_model_ids[0]
                    print(f"Model {model} not available, falling back to {model}")
                else:
                    return None, "No models available. Please check the API server."
        
        # Make a request to the API
        response = requests.get(
            f"{API_BASE_URL}/tts",
            params={
                "prompt": text,
                "voice": voice,
                "model": model
            },
            stream=True
        )
        
        if response.status_code != 200:
            error_text = response.text
            try:
                error_json = response.json()
                if "detail" in error_json:
                    error_text = error_json["detail"]
            except:
                pass
            return None, f"Error: {response.status_code} - {error_text}"
        
        # Save the audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Load the audio file using pydub
        audio = AudioSegment.from_wav(temp_file_path)
        
        # Convert to numpy array for Gradio
        samples = np.array(audio.get_array_of_samples())
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        return (audio.frame_rate, samples), "Speech generated successfully!"
    except Exception as e:
        return None, f"Error generating speech: {str(e)}"

def check_api_health():
    """Check if the API is running and models are loaded."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health_data = response.json()
            models_status = health_data.get("models", {})
            loaded_models = [model for model, status in models_status.items() if status == "loaded"]
            if loaded_models:
                return True, loaded_models
            else:
                return True, []
        return False, []
    except:
        return False, []

# Create the Gradio interface
def create_interface():
    # Get available voices
    voices = get_available_voices()
    
    with gr.Blocks(title="Orpheus TTS") as demo:
        gr.Markdown("# Orpheus Text-to-Speech")
        
        with gr.Row():
            with gr.Column():
                # Input text
                text_input = gr.Textbox(
                    label="Text to convert to speech",
                    placeholder="Enter text here...",
                    lines=5
                )
                
                # Voice selection
                voice_dropdown = gr.Dropdown(
                    choices=voices,
                    value="tara",
                    label="Voice"
                )
                
                # Model selection
                model_dropdown = gr.Dropdown(
                    choices=["finetune-prod", "pretrained"],
                    value="finetune-prod",
                    label="Model"
                )
                
                # Advanced options
                with gr.Accordion("Advanced Options", open=False):
                    temperature_slider = gr.Slider(
                        minimum=0.1,
                        maximum=1.0,
                        value=0.4,
                        step=0.1,
                        label="Temperature"
                    )
                    
                    repetition_penalty_slider = gr.Slider(
                        minimum=1.0,
                        maximum=2.0,
                        value=1.1,
                        step=0.1,
                        label="Repetition Penalty"
                    )
                
                # Generate button
                generate_button = gr.Button("Generate Speech")
            
            with gr.Column():
                # Output audio
                audio_output = gr.Audio(label="Generated Speech", type="numpy")
                
                # Status message
                status_message = gr.Textbox(label="Status", interactive=False)
        
        # Check API health and available models
        api_running, loaded_models = check_api_health()
        if not api_running:
            gr.Warning("Warning: API is not running. Make sure the API service is started.")
        elif not loaded_models:
            gr.Warning("Warning: No models are loaded. Check the API server.")
        else:
            # Update model dropdown with only loaded models
            model_dropdown.choices = loaded_models
            if model_dropdown.value not in loaded_models and loaded_models:
                model_dropdown.value = loaded_models[0]
        
        # Set up the button click event
        generate_button.click(
            fn=text_to_speech,
            inputs=[text_input, voice_dropdown, model_dropdown, temperature_slider, repetition_penalty_slider],
            outputs=[audio_output, status_message]
        )
        
        # Examples
        gr.Examples(
            examples=[
                ["Hello, my name is Tara. How are you doing today?", "tara", "finetune-prod"],
                ["I'm excited to demonstrate the capabilities of Orpheus TTS!", "leah", "finetune-prod"],
                ["This is an example of the Orpheus text-to-speech system.", "leo", "pretrained"]
            ],
            inputs=[text_input, voice_dropdown, model_dropdown]
        )
        
        # Add information about emotive tags
        gr.Markdown("""
        ## Emotive Tags
        
        You can add the following emotive tags to your text:
        - `<laugh>` - Add laughter
        - `<chuckle>` - Add a chuckle
        - `<sigh>` - Add a sigh
        - `<cough>` - Add a cough
        - `<sniffle>` - Add a sniffle
        - `<groan>` - Add a groan
        - `<yawn>` - Add a yawn
        - `<gasp>` - Add a gasp
        
        Example: "I just heard the funniest joke <laugh> it was about a chicken crossing the road."
        """)
    
    return demo

if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=args.server_port, share=os.environ.get("GRADIO_SHARE", "False").lower() == "true")