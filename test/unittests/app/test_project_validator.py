from miniworlds.base.project_validator import IssueCode, ProjectValidator, Severity


def test_nested_packages_and_assets_are_checked_without_virtual_environments(tmp_path):
    (tmp_path / 'main.py').write_text('from miniworlds import World\n')
    for folder in ('game', 'other', 'venv/lib', '.venv/lib', 'build'):
        target = tmp_path / folder
        target.mkdir(parents=True)
        (target / 'helper.py').write_text('import tkinter\n')
    images = tmp_path / 'images/levels'
    images.mkdir(parents=True)
    (images / 'background.tiff').write_bytes(b'asset')
    issues = ProjectValidator(tmp_path, tmp_path / 'main.py').validate()
    imports = [issue for issue in issues if issue.code == IssueCode.PROBLEMATIC_IMPORT]
    assert len(imports) == 2
    assert any('game/helper.py' in issue.message for issue in imports)
    assert any('other/helper.py' in issue.message for issue in imports)
    assert any('levels/background.tiff' in issue.message for issue in issues)


def test_optional_packages_warn_instead_of_preventing_export(tmp_path):
    (tmp_path / 'main.py').write_text('from miniworlds import World\nimport sqlite3\nimport requests\n')
    issues = ProjectValidator(tmp_path, tmp_path / 'main.py').validate()
    assert len(issues) == 2
    assert all(issue.web_severity == Severity.WARNING for issue in issues)


def test_thread_aliases_and_blocking_code_have_locations(tmp_path):
    (tmp_path / 'main.py').write_text('''from miniworlds import World
from threading import Thread as Worker
from time import sleep as pause
import concurrent.futures as futures
Worker(target=print).start()
futures.ThreadPoolExecutor()
pause(1)
while True:
    print("busy")
''')
    issues = ProjectValidator(tmp_path, tmp_path / 'main.py').validate()
    assert sum(issue.code == IssueCode.UNSUPPORTED_WEB_CALL for issue in issues) == 2
    assert sum(issue.code == IssueCode.BLOCKING_WEB_CODE for issue in issues) == 2
    assert all('main.py:' in issue.message for issue in issues)


def test_async_loops_and_thread_identity_are_allowed(tmp_path):
    (tmp_path / 'main.py').write_text('''from miniworlds import World
import threading
import asyncio
threading.get_ident()
async def update():
    while True:
        await asyncio.sleep(0)
while True:
    break
''')
    assert ProjectValidator(tmp_path, tmp_path / 'main.py').validate() == []


def test_nested_break_and_unused_async_function_do_not_hide_busy_loop(tmp_path):
    (tmp_path / 'main.py').write_text('''from miniworlds import World
import asyncio
while True:
    for value in range(10):
        break
    async def unused():
        await asyncio.sleep(0)
''')
    issues = ProjectValidator(tmp_path, tmp_path / 'main.py').validate()
    assert len(issues) == 1
    assert issues[0].code == IssueCode.BLOCKING_WEB_CODE
