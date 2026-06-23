# Development

## Setup development

1. Source `prepare.sh`

## Run tests

Run all tests with the canonical Docker path:

```sh
invoke tests.run
```

For repeated local development runs without rebuilding the image:

```sh
invoke tests.cached
```

If `invoke` is unavailable, run the equivalent Docker command from
[tasks.py](tasks.py).

Run a focused test through the Docker test path as well. Do not call `pytest`
directly from the host environment; use an Invoke task or open a Docker shell
through Invoke when you need an interactive focused run.

Example:

```sh
invoke tests.unit
```

Run visual tests through Docker too:

```sh
invoke tests.visual
```

Run the browser-runtime smoke tests with Pyodide and headless Chromium:

```sh
invoke tests.pyodide
```

Unit tests are grouped by domain under `test/unittests/<area>/`.

Task categories in [tasks.py](tasks.py):

- `tests.*`: Docker-based validation tasks
- `benchmarks.*`: benchmark and profiling scripts
- `build.docs`: local Sphinx build
- `build.image`: rebuild the shared Docker image for tests and benchmarks
- `deploy.push`: normal branch push workflow, optional with tags
- `deploy.release`: version bump, commit, tag, and optional
  push workflow
- `build.local` and `build.physics`: editable package installs
- `container.*`, `examples.checkout`: local utility tasks

Legacy flat task names still exist as compatibility aliases, but the grouped
names above are now the documented interface.

## Release and Docs

Build the documentation locally:

```sh
invoke build.docs
```

Create a release or preview it first:

```sh
invoke deploy.push
invoke deploy.push --tags
invoke deploy.release --revision
invoke deploy.release --patch --dry-run
invoke deploy.release --version=3.5.0.1
```

Upload new version to PyPI:

`deploy.release` accepts either an explicit `--version` or exactly one bump
flag:

- `--major`: next version like `4.0.0.0`
- `--minor`: next version like `3.6.0.0`
- `--patch`: next version like `3.5.1.0`
- `--revision`: next version like `3.5.0.6`

It synchronizes the version in both packages, runs the Docker test suite,
creates the commits and tags in the physics repository and the main
repository, and then pushes branch plus tag unless `--no-push` is used. After
the main tag is pushed, it creates the matching GitHub Release (with generated
release notes), which appears in the repository sidebar under **Releases**.

For a normal deploy without a version bump, use `deploy.push`. It pushes the
current branches in the main and physics repositories and can optionally push
all tags with `--tags`.

After the push step, GitHub Actions handle deployment automatically:

- pushing the main repository branch `main` triggers [deploy-docs.yml](.github/workflows/deploy-docs.yml)
- pushing `v*` tags triggers the PyPI publish workflows in the main and
  physics repositories

There is no manual docs upload task in `tasks.py`; docs deployment is owned
by the GitHub workflow.
