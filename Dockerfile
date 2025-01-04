# Basis-Image (Debian/Ubuntu für bessere Unterstützung)
FROM python:3.12-slim

# Installieren von Abhängigkeiten
RUN apt-get update && apt-get install -y \
    xvfb \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean
RUN pip install --no-cache-dir setuptools wheel
RUN pip install pytest

RUN pip install imgcompare

RUN apt-get install -y python3-tk
RUN apt-get update && apt-get install -y \
alsa-utils \
pulseaudio \
libasound2-dev \
&& apt-get clean



# Arbeitsverzeichnis einrichten
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install -r requirements.txt && echo "copied requirements txt" 

COPY source /app/source
RUN pip install -e /app/source


# Ihre Tests und pygame-Module kopieren
COPY test ./test


# Xvfb als virtuellen Framebuffer starten
CMD ["xvfb-run", "--server-args=-screen 0 1920x1080x24", "pytest", "test/", "-v"]
