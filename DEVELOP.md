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

If `invoke` is unavailable, run the equivalent Docker command from [tasks.py](tasks.py).

Run a single test:

Example:

```sh
pytest test/unittests/connectors/test_world_connector.py -v
```

Run a single visual test:

```sh
pytest test/visualtests/gui/test_610_toolbar_widgets.py -v
```

Unit tests are grouped by domain under `test/unittests/<area>/`.

Task categories in [tasks.py](tasks.py):

- `tests.*`: Docker-based validation tasks
- `benchmarks.*`: benchmark and profiling scripts
- `build.docs`: local Sphinx build
- `build.image`: rebuild the shared Docker image for tests and benchmarks
- `deploy.release`: version bump, commit, tag, and optional push workflow
- `build.local` and `build.physics`: editable package installs
- `container.*`, `examples.checkout`: local utility tasks

Legacy flat task names still exist as compatibility aliases, but the grouped names above are now the documented interface.

## Release and Docs

Build the documentation locally:

```sh
invoke build.docs
```

Create a release or preview it first:

```sh
invoke deploy.release --revision
invoke deploy.release --patch --dry-run
invoke deploy.release --version=3.5.0.1
```

Upload new version to PyPI:

`deploy.release` accepts either an explicit `--version` or exactly one bump flag:

- `--major`: next version like `4.0.0.0`
- `--minor`: next version like `3.6.0.0`
- `--patch`: next version like `3.5.1.0`
- `--revision`: next version like `3.5.0.6`

It synchronizes the version in both packages, runs the Docker test suite,
creates the commits and tags in the physics repository and the main repository,
and then pushes branch plus tag unless `--no-push` is used.

After that push step, GitHub Actions handle deployment automatically:

- pushing the main repository branch `main` triggers [deploy-docs.yml](.github/workflows/deploy-docs.yml)
- pushing `v*` tags triggers the PyPI publish workflows in the main and physics repositories

There is no manual docs upload task in `tasks.py`; docs deployment is owned by the GitHub workflow.
