## Setup development

1. Source `prepare.sh`

## Run tests

Run all tests:

```
invoke run-tests
```

Run a single test:

Example:
```
python -m test.test_610_toolbar_widgets 
```

## Docs


Upload new version to pypi:

```
git tag v3.0.1.1  
# Replace version number and set this number in source/setup.conf

git push origin v3.0.1.1
```