FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel
RUN pip install uv

RUN apt update && \
    apt install -y espeak-ng git git-lfs && \
    rm -rf /var/lib/apt/lists/*
    
RUN pip3 install --upgrade --no-cache-dir torch==2.5.1 torchvision==0.20.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

RUN git clone https://github.com/canopyai/Orpheus-TTS /Orpheus-TTS
WORKDIR /Orpheus-TTS
RUN pip install -r requirements.txt
RUN mkdir -p pretrained_models

# Install Gradio and other dependencies for the web UI
RUN pip install gradio pydub requests numpy

# Set PYTHONPATH
ENV PYTHONPATH=/Orpheus-TTS

# Make port 7325 available to the world outside this container
EXPOSE 7325

# Run app.py when the container launches
CMD ["sh", "-c", "python -u webui.py --device 0 --server_port ${PORT}"]

