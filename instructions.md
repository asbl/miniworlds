# Development Instructions

## Environment Setup

Use the project setup script from the repository root:

```sh
source prepare.sh
```

The script creates `venv` if needed, activates it, installs `requirements.txt`,
prepends `venv/bin` to `PATH`, and lists the available Invoke tasks.

If the shell was not prepared in the current session, call Invoke through the
venv explicitly:

```sh
venv/bin/invoke --list
```

The same setup is also available as Invoke tasks, which call `source prepare.sh`
internally:

```sh
venv/bin/invoke env.prepare
venv/bin/invoke env.check
```

Use `env.check` when a task needs the local Miniworlds and
`miniworlds_physics` imports to work outside Docker. It verifies the venv,
`pygame`, `pymunk`, `miniworlds`, and `miniworlds_physics` with the correct
`PYTHONPATH`.

## Tests

Always start Miniworlds tests through Invoke so they run inside the Docker
environment defined in `tasks.py`. Do not run `pytest` directly for validation,
including focused or single-file test runs.

The canonical test tasks run inside the Docker image configured by `tasks.py`.
Use these Docker tasks when evaluating test failures. In particular, visual
test output depends on the operating system, fonts, and rendering libraries, so
visual baselines must only be compared or updated from the Docker environment.
Do not accept or regenerate visual baselines from a direct local `pytest` run.

Run all unit tests:

```sh
venv/bin/invoke tests.unit
```

Run all visual tests:

```sh
venv/bin/invoke tests.visual
```

Run the full test suite and rebuild the Docker image first:

```sh
venv/bin/invoke tests.run
```

Run the full test suite against the current Docker image without rebuilding:

```sh
venv/bin/invoke tests.cached
```

Run the focused `miniworlds_physics` integration tests locally with the prepared
venv and the required `PYTHONPATH`:

```sh
venv/bin/invoke tests.physics
```

The equivalent legacy task names are also available:

```sh
venv/bin/invoke run-unit-tests
venv/bin/invoke run-visual-tests
venv/bin/invoke run-tests
venv/bin/invoke run-tests-cached
venv/bin/invoke run-physics-tests
```

## Publishing submodule libraries to PyPI

The standalone submodule libraries each have their own GitHub repository and
publish to PyPI from their own CI workflow. Each submodule contains
`.github/workflows/publish_to-pypi.yml`, which builds and uploads the package
when a `v*` tag is pushed to that submodule's remote.

| Submodule                          | GitHub repo                      | PyPI package        |
|------------------------------------|----------------------------------|---------------------|
| `libraries/miniworlds_robot`       | `asbl/miniworlds-robot`          | `miniworlds-robot`  |
| `libraries/miniworlds_turtle`      | `asbl/miniworlds-turtle`         | `miniworlds-turtle` |

The main repo's
[publish_to-pypi.yml](.github/workflows/publish_to-pypi.yml) is separate; it
publishes only the `miniworlds` core and `miniworlds-data` packages from this
repo and does **not** touch the submodule libraries.

### Required GitHub secret

Each submodule repository must have the secret `PYPI_API_TOKEN` configured
under **Settings → Secrets and variables → Actions**. The token is a PyPI
API token (scope: the specific project, or "Entire account"). Without it the
workflow run will fail at the `twine upload` step.

### Release workflow (CI publishes automatically)

Run all steps from inside the submodule directory, e.g.
`libraries/miniworlds_robot`. Replace `<version>` below with the concrete
value from that submodule's `pyproject.toml`.

1. Check the submodule is clean and committed:
   ```sh
   cd libraries/miniworlds_robot
   git status -s            # must be empty
   ```
2. Read the current version and confirm the intended bump:
   ```sh
   grep '^version' pyproject.toml
   ```
3. Bump `version = "..."` in `pyproject.toml` to the new release (e.g.
   `0.1.3` → `0.1.4`), commit, tag, and push:
   ```sh
   git commit -am "Bump version to <version>"
   git tag v<version>
   git push origin main --tags
   ```
   Pushing the `v*` tag triggers the submodule's `publish_to-pypi.yml`
   workflow on GitHub Actions, which builds and uploads to PyPI.
4. Update the parent repo's submodule pointer so the main repo tracks the new
   release:
   ```sh
   cd /home/sbl/code-git/miniworlds
   git add libraries/miniworlds_robot
   git commit -m "Update miniworlds_robot submodule to v<version>"
   ```
   (Push the parent repo as a separate step following the normal deploy flow.)
5. Watch the workflow run on GitHub: navigate to the submodule repository's
   **Actions** tab and confirm the "Publish to PyPI" run for `v<version>`
   succeeds. The upload step can take 1–2 minutes.
6. Verify the release is visible (the `pip index` cache lags; query the API
   directly):
   ```sh
   venv/bin/python -c \
     "import urllib.request, json; d=json.load(urllib.request.urlopen('https://pypi.org/pypi/<pypi-name>/json')); print('latest:', d['info']['version']); print('versions:', sorted(d['releases'].keys()))"
   ```
   (`<pypi-name>` is `miniworlds-robot` or `miniworlds-turtle`.)

### Manual upload (fallback)

Use this only if CI is unavailable or the workflow run fails and a quick
retry is needed without fixing CI first.

Prerequisites:

- `build` and `twine` are not in `requirements.txt`; install them into the
  project venv first:
  ```sh
  venv/bin/pip install --upgrade build twine
  ```
- The PyPI token lives in the parent repo's `.env` as
  `pypi_token = <value>` (note the spaces around `=` — the file is **not**
  shell-sourceable). Read it with awk, never echo or log the value.

Steps (run from inside the submodule directory):

```sh
# Build
rm -rf dist build *.egg-info
venv/bin/python -m build
ls dist/   # expect <pypi-name>-<version>-py3-none-any.whl and .tar.gz

# Upload with the token from .env
TOKEN=$(awk -F'=' '/^[[:space:]]*pypi_token[[:space:]]*=/{gsub(/^[[:space:]]+|[[:space:]]+$/,"",$2); gsub(/^["'"'"']|["'"'"']$/,"",$2); print $2}' /home/sbl/code-git/miniworlds/.env)
TWINE_USERNAME='__token__' TWINE_PASSWORD="$TOKEN" \
  venv/bin/twine upload --non-interactive dist/*
```

### Notes and pitfalls

- Pushing a `v*` tag to the submodule remote is what triggers publication.
  Committing and pushing `main` alone does **not** publish.
- A tag alone is not a release until the workflow (or a manual upload) runs.
  Before CI existed, tags `v0.1.1` and `v0.1.2` were pushed to the robot
  remote but never uploaded to PyPI.
- PyPI does not allow re-uploading the same version. If a build is broken,
  bump the version instead of trying to overwrite.
- Keep the parent repo's submodule pointer in sync, otherwise the main repo
  still pins the old library commit.
- The workflow uses `python-version: '3.10'`, matching the
  `requires-python = ">=3.10"` declared in each submodule's `pyproject.toml`.
