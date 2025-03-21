FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Gradio and other dependencies for the web UI
# We don't need orpheus-speech since the Gradio interface will use the API
RUN pip install --no-cache-dir gradio pydub requests numpy

# Copy the web UI files
COPY webui /app
WORKDIR /app

# Make port 7325 available to the world outside this container
EXPOSE 7325

# Run the Gradio app when the container launches
CMD ["python", "-u", "webui.py", "--server_port", "${PORT}"]

