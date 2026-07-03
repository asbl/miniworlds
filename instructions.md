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
publish a separate PyPI package. They are **not** covered by the main repo's
[publish_to-pypi.yml](.github/workflows/publish_to-pypi.yml) (which handles
only the `miniworlds` core and `miniworlds-data`), so each release must be
uploaded manually.

| Submodule                          | GitHub repo                      | PyPI package        |
|------------------------------------|----------------------------------|---------------------|
| `libraries/miniworlds_robot`       | `asbl/miniworlds-robot`          | `miniworlds-robot`  |
| `libraries/miniworlds_turtle`      | `asbl/miniworlds-turtle`         | `miniworlds-turtle` |

### Prerequisites

- `build` and `twine` are not in `requirements.txt`; install them into the
  project venv first:
  ```sh
  venv/bin/pip install --upgrade build twine
  ```
- The PyPI token lives in the parent repo's `.env` as
  `pypi_token = <value>` (note the spaces around `=` — the file is **not**
  shell-sourceable). Read it with awk, never echo or log the value.

### Release workflow (manual upload)

Run all steps from inside the submodule directory, e.g.
`libraries/miniworlds_robot`. Replace `<lib>`, `<version>`, and `<pypi-name>`
below with the concrete values from that submodule's `pyproject.toml`.

1. Check the submodule is clean, committed, and pushed:
   ```sh
   cd libraries/miniworlds_robot
   git status -s            # must be empty
   git log origin/main..HEAD # must be empty (everything pushed)
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
4. Update the parent repo's submodule pointer so the main repo tracks the new
   release:
   ```sh
   cd /home/sbl/code-git/miniworlds
   git add libraries/miniworlds_robot
   git commit -m "Update miniworlds_robot submodule to v<version>"
   ```
   (Push the parent repo as a separate step following the normal deploy flow.)
5. Build the distribution from inside the submodule directory:
   ```sh
   cd libraries/miniworlds_robot
   rm -rf dist build *.egg-info
   venv/bin/python -m build
   ls dist/   # expect <pypi-name>-<version>-py3-none-any.whl and .tar.gz
   ```
6. Upload to PyPI using the token from `.env`:
   ```sh
   TOKEN=$(awk -F'=' '/^[[:space:]]*pypi_token[[:space:]]*=/{gsub(/^[[:space:]]+|[[:space:]]+$/,"",$2); gsub(/^["'"'"']|["'"'"']$/,"",$2); print $2}' /home/sbl/code-git/miniworlds/.env)
   TWINE_USERNAME='__token__' TWINE_PASSWORD="$TOKEN" \
     venv/bin/twine upload --non-interactive dist/*
   ```
7. Verify the release is visible (the `pip index` cache lags; query the API
   directly):
   ```sh
   venv/bin/python -c \
     "import urllib.request, json; d=json.load(urllib.request.urlopen('https://pypi.org/pypi/<pypi-name>/json')); print('latest:', d['info']['version']); print('versions:', sorted(d['releases'].keys()))"
   ```
   (`<pypi-name>` is `miniworlds-robot` or `miniworlds-turtle`.)

### Notes and pitfalls

- A tag alone is not a release. Before CI existed, tags `v0.1.1` and `v0.1.2`
  were pushed to the robot remote but never uploaded to PyPI. The build +
  twine upload in step 5–6 is what actually publishes.
- PyPI does not allow re-uploading the same version. If a build is broken,
  bump the version instead of trying to overwrite.
- Keep the parent repo's submodule pointer in sync (step 4), otherwise the
  main repo still pins the old library commit.

### Status of CI auto-publish

Each submodule has a prepared `publish_to-pypi.yml` workflow that would build
and upload automatically when a `v*` tag is pushed. These workflows are
committed locally in `libraries/miniworlds_robot/.github/workflows/` and
`libraries/miniworlds_turtle/.github/workflows/`, and the matching
`PYPI_API_TOKEN` secret has been added to both GitHub repos, **but the
workflow files are not yet pushed to the remotes** because the push needs a
Personal Access Token with the `workflow` scope. Until that token is available,
use the manual upload above. To activate CI later: set a PAT with `workflow`
scope, push the submodule commits, and from then on pushing a `v*` tag will
publish automatically.
