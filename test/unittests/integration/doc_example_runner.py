from __future__ import annotations

import os
import re
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from miniworlds import App
from miniworlds.worlds.world import World
from test.unittests import REPO_ROOT, UNITTESTS_ROOT_FILE


DEFAULT_TIMEOUT_SECONDS = 10
PLACEHOLDER_IMAGE_NAMES = {
    "background.png",
    "cow.png",
    "drive1.png",
    "grass.png",
    "knight.png",
    "player.png",
    "ship.png",
    "wall.png",
}
IMAGE_PATH_RE = re.compile(r"""["'](?P<path>images/[^"']+)["']""")


def _cleanup_imports(script_dir: Path, existing_modules: dict[str, object]) -> None:
    script_dir = script_dir.resolve()
    for module_name, module in list(sys.modules.items()):
        if module_name in existing_modules:
            continue
        module_file = getattr(module, "__file__", None)
        if not module_file:
            continue
        try:
            if Path(module_file).resolve().is_relative_to(script_dir):
                sys.modules.pop(module_name, None)
        except FileNotFoundError:
            continue


def _write_placeholder_image(path: Path) -> None:
    import pygame

    path.parent.mkdir(parents=True, exist_ok=True)
    surface = pygame.Surface((2, 2), pygame.SRCALPHA)
    surface.fill((255, 0, 255, 255))
    if path.suffix:
        pygame.image.save(surface, os.fspath(path))
        return
    png_path = path.with_name(f"{path.name}.png")
    pygame.image.save(surface, os.fspath(png_path))
    path.write_bytes(png_path.read_bytes())
    png_path.unlink()


def _create_placeholder_project(script_path: Path, project_dir: Path) -> Path:
    source = script_path.read_text(encoding="utf-8")
    images_dir = project_dir / "images"
    images_dir.mkdir()
    image_paths = {images_dir / name for name in PLACEHOLDER_IMAGE_NAMES}
    image_paths.update(project_dir / match.group("path") for match in IMAGE_PATH_RE.finditer(source))
    for image_path in image_paths:
        _write_placeholder_image(image_path)
    project_script = project_dir / script_path.name
    project_script.write_text(source, encoding="utf-8")
    return project_script


def _run_doc_example_in_worker(source_script_path: Path) -> None:
    source_script_path = source_script_path.resolve()
    original_run = World.run
    observed_frames: list[int] = []

    def smoke_run(world, *args, **kwargs):
        world.app._unittest = True
        world.mouse._tracked_position = (20, 20)

        @world.register
        def act(self):
            if self.frame >= 3:
                self.quit()

        result = original_run(world, *args, **kwargs)
        observed_frames.append(world.frame)
        return result

    with tempfile.TemporaryDirectory(prefix="miniworlds-doc-example-") as temp_dir:
        script_path = _create_placeholder_project(source_script_path, Path(temp_dir))
        old_cwd = os.getcwd()
        old_path = list(sys.path)
        existing_modules = dict(sys.modules)
        script_dir = script_path.parent

        try:
            App.reset(unittest=True, file=os.fspath(script_path))
            os.chdir(script_dir)
            script_dir_str = os.fspath(script_dir)
            if script_dir_str not in sys.path:
                sys.path.insert(0, script_dir_str)

            with patch.object(App, "check_for_run_method", return_value=None):
                with patch.object(World, "run", smoke_run):
                    runpy.run_path(os.fspath(script_path), run_name="__main__")
        except Exception as error:
            raise AssertionError(
                f"Documentation example failed: {source_script_path}"
            ) from error
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            _cleanup_imports(script_dir, existing_modules)
            App.reset(unittest=True, file=str(UNITTESTS_ROOT_FILE))


def run_doc_example_script(script_path: Path, metadata: dict[str, object]) -> None:
    """Execute a generated documentation example in an isolated process."""
    timeout = int(os.environ.get("MINIWORLDS_DOC_EXAMPLE_TIMEOUT", DEFAULT_TIMEOUT_SECONDS))
    env = os.environ.copy()
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env.setdefault("MINIWORLDS_TEST_FAST", "1")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "test.unittests.integration.doc_example_runner",
                os.fspath(script_path),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        source = f"{metadata.get('docs_path')}:{metadata.get('line')}"
        raise AssertionError(
            f"Documentation example timed out after {timeout}s: {source}"
        ) from error

    if result.returncode != 0:
        source = f"{metadata.get('docs_path')}:{metadata.get('line')}"
        output = (result.stdout + result.stderr).strip()
        raise AssertionError(
            f"Documentation example failed: {source}\n{output}"
        )


if __name__ == "__main__":
    _run_doc_example_in_worker(Path(sys.argv[1]))
