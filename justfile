# Setzen Sie die Standard-Shell für die Befehle
set shell := ["bash", "-cu"]

# Variablen
image := "pygame-tests"
container := "pygame-test-container"

# Docker-Image erstellen
build:
    docker build -t {{image}} .

# Tests im Container ausführen
test:
    docker run --rm \
    --user $(id -u):$(id -g) \
    -v $(pwd)/test/outputfiles:/app/test/outputfiles \
    -v $(pwd)/test/testfiles:/app/test/testfiles \
    pygame-tests pytest test/ -v

# Interaktives Debugging des Containers
debug:
    docker run --rm -it {{image}} bash

# Cleanup - Nicht verwendete Images und Container entfernen
cleanup:
    docker system prune -f

# Container starten und eine grafische Debugging-Umgebung bereitstellen
debug-x11:
    xhost +local:root
    docker run --rm -it \
        -e DISPLAY=$DISPLAY \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        {{image}} bash
    xhost -local:root
