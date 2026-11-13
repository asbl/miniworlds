"""Version policy and transactional repairs without network or real pip writes."""

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

from test.unittests.thonny_plugin.test_learning_tools import ROOT

pytestmark = pytest.mark.unit


def load(name):
    path = (
        ROOT / "libraries/thonny-miniworlds/thonnycontrib/miniworlds" / (name + ".py")
    )
    spec = importlib.util.spec_from_file_location("miniworlds_test_" + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


worker = load("maintenance")
updates = load("updates")


def test_versions_ignore_yanked_prerelease_and_incompatible_python():
    def entry(version, requires=">=3.10", **kwargs):
        return dict(
            filename=f"miniworlds-{version}-py3-none-any.whl",
            **{"requires-python": requires},
            **kwargs,
        )

    data = {
        "files": [
            entry("4.4.0.9"),
            entry("4.5", ">=3.12"),
            entry("5.0rc1"),
            entry("6", yanked=True),
            entry("100", "not-a-specifier"),
            {"filename": "another_package-999-py3-none-any.whl"},
        ]
    }
    versions = updates.release_versions(data, "3.10.9")
    assert versions == {"latest": "4.5", "compatible": "4.4.0.9"}
    assert "Update verfügbar" in updates.version_message("4.3", versions)
    assert "aktuell" in updates.version_message(
        "4.4.0.9", {"latest": "4.4.0.9", "compatible": "4.4.0.9"}
    )
    assert "Entwicklungsversion" in updates.version_message(
        "4.6", {"latest": "4.5", "compatible": "4.5"}
    )
    offline = updates.version_message("4.4.0.9", {"error": "offline"})
    assert "aktuell" not in offline and "nicht festgestellt" in offline
    assert "noch nicht installiert" in updates.version_message(None, versions)


def test_numeric_version_order_and_no_release():
    data = {"files": [{"filename": f"miniworlds-{v}.tar.gz"} for v in ["4.9", "4.10"]]}
    assert updates.release_versions(data, "3.12")["latest"] == "4.10"
    with pytest.raises(ValueError):
        updates.release_versions({"files": []}, "3.12")


@pytest.mark.parametrize(
    "log, word",
    [
        ("uninstall-no-record-file", "Sicherung"),
        ("SSL certificate verify failed", "Schulnetz"),
        ("externally-managed-environment", "virtuelle"),
        ("WinError 32", "gesperrt"),
        ("No module named pip", "pip fehlt"),
    ],
)
def test_failure_hints(log, word):
    assert word in updates.installation_hint(log)


@pytest.fixture
def repair_environment(tmp_path, monkeypatch):
    root = tmp_path / "site-packages"
    root.mkdir()
    package = root / "miniworlds"
    package.mkdir()
    (package / "__init__.py").write_text("# original student-independent library\n")
    dist = root / "miniworlds-1.0.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text("Name: miniworlds\nVersion: 1.0\n")
    # Intentionally no RECORD: this is the failure the repair must recover from.
    extension = root / "miniworlds_physics"
    extension.mkdir()
    (extension / "keep.py").write_text("do not change")
    env = {
        "root": str(root),
        "managed": False,
        "user": False,
        "user_enabled": True,
        "pip": True,
        "executable": sys.executable,
        "python": "3.12",
        "venv": True,
    }
    monkeypatch.setattr(worker, "environment", lambda: env.copy())

    def inspect():
        return dict(
            env,
            version="2.0" if (root / "miniworlds-2.0.dist-info").exists() else "1.0",
            module=str(package / "__init__.py"),
            issues=[],
            editable=False,
        )

    monkeypatch.setattr(worker, "inspect_installation", inspect)
    commands = []

    def pip(arguments):
        commands.append(arguments)
        if arguments[0] == "download":
            target = Path(arguments[arguments.index("--dest") + 1])
            with zipfile.ZipFile(
                target / "miniworlds-2.0-py3-none-any.whl", "w"
            ) as archive:
                archive.writestr("miniworlds/__init__.py", "# new library\n")
        elif "--force-reinstall" in arguments:
            assert not dist.exists(), "old metadata must already be backed up"
            package.mkdir()
            (package / "__init__.py").write_text("# new library\n")
            new_dist = root / "miniworlds-2.0.dist-info"
            new_dist.mkdir()
            (new_dist / "METADATA").write_text("Name: miniworlds\nVersion: 2.0\n")

    monkeypatch.setattr(worker, "run_pip", pip)
    return root, package, dist, commands, pip


def test_repair_backs_up_corrupt_package_and_only_changes_miniworlds(
    repair_environment, tmp_path
):
    root, package, dist, commands, _ = repair_environment
    result = worker.repair(tmp_path / "backups")
    backup = Path(result["backup"])
    assert (package / "__init__.py").read_text() == "# new library\n"
    assert (backup / "miniworlds" / "__init__.py").read_text().startswith("# original")
    assert (backup / dist.name / "METADATA").is_file()
    assert (root / "miniworlds_physics" / "keep.py").read_text() == "do not change"
    manifest = json.loads((backup / "manifest.json").read_text())
    assert manifest["state"] == "complete"
    assert commands[0][0] == "download"
    assert "--no-index" in commands[1] and "--no-deps" in commands[1]
    assert "--force-reinstall" not in commands[-1]


def test_failed_install_restores_old_package_and_metadata(
    repair_environment, tmp_path, monkeypatch
):
    root, package, dist, _commands, fake = repair_environment

    def fail_after_writing(arguments):
        fake(arguments)
        if "--force-reinstall" in arguments:
            raise RuntimeError("simulated pip failure after partial write")

    monkeypatch.setattr(worker, "run_pip", fail_after_writing)
    with pytest.raises(RuntimeError, match="simulated"):
        worker.repair(tmp_path / "backups")
    assert (package / "__init__.py").read_text().startswith("# original")
    assert dist.exists() and not (root / "miniworlds-2.0.dist-info").exists()
    manifest = next((tmp_path / "backups").glob("*/manifest.json"))
    assert json.loads(manifest.read_text())["state"] == "restored"
    assert (
        manifest.parent / "failed-installation" / "miniworlds" / "__init__.py"
    ).exists()


def test_download_failure_leaves_original_untouched(
    repair_environment, tmp_path, monkeypatch
):
    _, package, dist, _, _ = repair_environment

    def offline(arguments):
        raise RuntimeError("network offline")

    monkeypatch.setattr(worker, "run_pip", offline)
    with pytest.raises(RuntimeError, match="offline"):
        worker.repair(tmp_path / "backups")
    assert (package / "__init__.py").read_text().startswith("# original")
    assert dist.exists()


def test_symlinks_and_foreign_metadata_are_not_moved(tmp_path):
    root = tmp_path / "site"
    root.mkdir()
    target = tmp_path / "project"
    target.mkdir()
    (root / "miniworlds").symlink_to(target, target_is_directory=True)
    with pytest.raises(RuntimeError, match="normale Paketinstallation"):
        worker.repair_candidates(root)
    (root / "miniworlds").unlink()
    dist = root / "miniworlds-2.0.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text("Name: unrelated\n")
    with pytest.raises(RuntimeError, match="anderen Paket"):
        worker.repair_candidates(root)
    assert dist.exists()


def test_pep668_is_never_overridden(repair_environment, tmp_path, monkeypatch):
    root, _, _, commands, _ = repair_environment
    info = worker.environment()
    info["managed"] = True
    monkeypatch.setattr(worker, "environment", lambda: info)
    with pytest.raises(RuntimeError, match="PEP 668"):
        worker.install()
    with pytest.raises(RuntimeError, match="PEP 668"):
        worker.repair(tmp_path / "backups")
    assert commands == []
    assert (root / "miniworlds").exists()


def test_inspection_detects_missing_record_files_and_orphan_metadata(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    root = tmp_path / "site-packages"
    root.mkdir()
    package = root / "miniworlds"
    package.mkdir()
    module = package / "__init__.py"
    module.write_text("")
    dist = root / "miniworlds-1.0.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text("Name: miniworlds\nVersion: 1.0\n")
    env = {"root": str(root)}
    monkeypatch.setattr(worker, "environment", lambda: env.copy())
    monkeypatch.setattr(
        worker.metadata,
        "distributions",
        lambda: [worker.metadata.Distribution.at(dist)],
    )
    monkeypatch.setattr(
        worker.importlib.util,
        "find_spec",
        lambda name: SimpleNamespace(origin=str(module)),
    )
    assert any("RECORD" in issue for issue in worker.inspect_installation()["issues"])
    (dist / "RECORD").write_text("miniworlds/__init__.py,,\nminiworlds/missing.py,,\n")
    assert any(
        "Bibliotheksdateien fehlen" in issue
        for issue in worker.inspect_installation()["issues"]
    )
    monkeypatch.setattr(worker.metadata, "distributions", list)
    assert any(
        "Paketinformationen fehlen" in issue
        for issue in worker.inspect_installation()["issues"]
    )


@pytest.mark.network
@pytest.mark.skipif(
    __import__("os").environ.get("MINIWORLDS_TEST_INSTALLER_NETWORK") != "1",
    reason="explicit opt-in for disposable pip repair against PyPI",
)
def test_real_pip_repairs_missing_record_in_disposable_venv(tmp_path):
    import subprocess

    subprocess.run(
        [sys.executable, "-m", "venv", str(tmp_path / "venv")],
        check=True,
        capture_output=True,
        timeout=60,
    )
    python = str(tmp_path / "venv/bin/python")
    subprocess.run(
        [python, "-I", "-m", "pip", "install", "--no-deps", "miniworlds"],
        check=True,
        capture_output=True,
        timeout=120,
    )
    code = """import sysconfig
from pathlib import Path
root=Path(sysconfig.get_path('purelib'))
next(root.glob('miniworlds-*.dist-info/RECORD')).unlink()
p=root/'miniworlds_physics'
p.mkdir()
(p/'keep.py').write_text('untouched')
print(root)
"""
    root = Path(
        subprocess.run(
            [python, "-c", code], check=True, capture_output=True, text=True
        ).stdout.strip()
    )
    script = str(
        ROOT / "libraries/thonny-miniworlds/thonnycontrib/miniworlds/maintenance.py"
    )
    before = subprocess.run(
        [python, "-I", script, "inspect"], check=True, capture_output=True, text=True
    )
    assert "RECORD" in before.stdout
    outcome = subprocess.run(
        [python, "-I", script, "repair", "--backup-root", str(tmp_path / "backups")],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr
    result = json.loads(
        next(
            line[len(worker.RESULT_PREFIX) :]
            for line in outcome.stdout.splitlines()
            if line.startswith(worker.RESULT_PREFIX)
        )
    )
    assert result["ok"] and not result["issues"]
    assert (root / "miniworlds_physics/keep.py").read_text() == "untouched"
    assert list((Path(result["backup"])).glob("miniworlds-*.dist-info/METADATA"))
    assert list(root.glob("miniworlds-*.dist-info/RECORD"))
    assert updates.fetch_versions(result["python"])["compatible"]
