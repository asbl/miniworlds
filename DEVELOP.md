# Development

## Setup development

1. Source `prepare.sh`

## Run tests

Run all tests with the canonical Docker path:

```sh
invoke run_tests
```

For repeated local development runs without rebuilding the image:

```sh
invoke run_tests_cached
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

## Docs

Upload new version to pypi:

```sh
git tag v3.0.1.1  
# Replace version number and set this number in source/setup.conf

git push origin v3.0.1.1
```
