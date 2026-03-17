from pathlib import Path


UNITTESTS_ROOT = Path(__file__).resolve().parent
UNITTESTS_ROOT_FILE = UNITTESTS_ROOT / "__init__.py"
REPO_ROOT = UNITTESTS_ROOT.parent.parent