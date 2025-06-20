# Base image with Python 3.12 (slim variant)
FROM python:3.12-slim

# Install required system dependencies for GUI, audio, and testing
RUN apt-get update && apt-get install -y \
    xvfb \                      
    libgl1-mesa-glx \           
    libglib2.0-0 \              
    alsa-utils \                
    pulseaudio \                
    libasound2-dev \            
    python3-tk \                
    && apt-get clean

# Install Python tools and test dependencies
RUN pip install --no-cache-dir setuptools wheel
RUN pip install pytest imgcompare

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt && echo "copied requirements txt"

# Copy source code and install it as editable
COPY source /app/source
RUN pip install -e /app/source

# Copy test files
COPY test ./test

# Give full write permissions to /app (fixes PytestCacheWarning)
RUN chmod -R 777 /app


# Run tests:
# - xvfb-run sets up a virtual display (needed for GUI tests)
# - "-p no:cacheprovider" disables pytest's cache plugin to avoid permission warnings
CMD ["xvfb-run", "--server-args=-screen 0 1920x1080x24", "pytest", "test/", "-v", "-p", "no:cacheprovider"]
