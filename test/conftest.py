import os

# Vorbereitungen, die vor den Tests ausgeführt werden sollen
def pytest_configure(config):
    print("Setup vor allen Tests wird ausgeführt.")
    os.environ["SDL_AUDIODRIVER"] = "dummy"