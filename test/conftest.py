import os
import warnings

# Vorbereitungen, die vor den Tests ausgeführt werden sollen
def pytest_configure(config):
    print("Setup vor allen Tests wird ausgeführt.")
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    warnings.filterwarnings(
        "ignore",
        message=r".*\.run\(\) was not found in your code.*",
        category=UserWarning,
        module=r"miniworlds\.base\.app"
    )
