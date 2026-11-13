"""Standalone worker for the selected interpreter; only the standard library.

Run by absolute filename with -I. The target does not need the Thonny plugin.
No pupil program is imported, and no operating-system protection is bypassed.
"""

import argparse
import csv
import importlib
import importlib.util
import io
import json
import re
import shutil
import site
import subprocess
import sys
import sysconfig
import tempfile
import time
import zipfile
from importlib import metadata
from pathlib import Path

RESULT_PREFIX = "MINIWORLDS_RESULT:"


def normalized(name):
    return re.sub(r"[-_.]+", "-", name or "").lower()


def environment():
    venv = sys.prefix != sys.base_prefix
    user = not venv
    root = Path(site.getusersitepackages() if user else sysconfig.get_path("purelib"))
    managed = (
        not venv
        and (Path(sysconfig.get_path("stdlib")) / "EXTERNALLY-MANAGED").exists()
    )
    return {
        "executable": sys.executable,
        "python": sys.version.split()[0],
        "venv": venv,
        "managed": managed,
        "user": user,
        "root": str(root.absolute()),
        "pip": importlib.util.find_spec("pip") is not None,
        "user_enabled": bool(site.ENABLE_USER_SITE) if user else True,
    }


def inspect_installation():
    result = environment()
    result.update(version=None, location=None, issues=[], editable=False)
    distributions = []
    try:
        distributions = [
            d
            for d in metadata.distributions()
            if normalized(d.metadata.get("Name")) == "miniworlds"
        ]
    except (OSError, ValueError, UnicodeError) as error:
        result["issues"].append(f"Paketinformationen sind nicht lesbar: {error}")
    if distributions:
        distribution = distributions[0]
        result["version"] = distribution.version
        result["location"] = str(distribution.locate_file(""))
        try:
            direct = json.loads(distribution.read_text("direct_url.json") or "{}")
            result["editable"] = bool(direct.get("dir_info", {}).get("editable"))
            record = distribution.read_text("RECORD")
            if record is None:
                result["issues"].append(
                    "Die Dateiliste (RECORD) fehlt. pip kann die Installation möglicherweise nicht ersetzen."
                )
            else:
                missing = [
                    str(f)
                    for row in csv.reader(io.StringIO(record))
                    if row
                    for f in [row[0]]
                    if str(f).replace("\\", "/").startswith("miniworlds/")
                    and str(f).endswith(".py")
                    and not Path(distribution.locate_file(f)).is_file()
                ]
                if missing:
                    result["issues"].append(
                        f"{len(missing)} Bibliotheksdateien fehlen, z. B. {missing[0]}."
                    )
        except (OSError, ValueError, UnicodeError) as error:
            result["issues"].append(f"Paketdateien sind beschädigt: {error}")
    if len(distributions) > 1:
        result["issues"].append(
            "Mehrere miniworlds-Paketinformationen gefunden; Version und Import können voneinander abweichen."
        )
    spec = importlib.util.find_spec("miniworlds")
    result["module"] = str(spec.origin) if spec and spec.origin else None
    if (
        result["module"] or (Path(result["root"]) / "miniworlds").exists()
    ) and not distributions:
        result["issues"].append(
            "miniworlds-Dateien sind vorhanden, aber die Paketinformationen fehlen."
        )
    if distributions and not result["module"]:
        result["issues"].append(
            "Paketinformationen sind vorhanden, aber das miniworlds-Modul fehlt."
        )
    return result


def ensure_writable_environment(info):
    if info["managed"]:
        raise RuntimeError(
            "Diese Python-Installation wird vom Betriebssystem verwaltet (PEP 668). Bitte eine virtuelle Umgebung wählen."
        )
    if not info["user_enabled"]:
        raise RuntimeError(
            "In diesem Interpreter ist die Installation im Benutzerverzeichnis deaktiviert. Bitte eine virtuelle Umgebung wählen."
        )
    if sys.version_info < (3, 10):  # noqa: UP036 -- standalone worker may run in an older backend
        raise RuntimeError("miniworlds benötigt Python ab Version 3.10.")
    if not info["pip"]:
        raise RuntimeError(
            "pip fehlt in diesem Interpreter. Bitte die virtuelle Umgebung mit pip neu anlegen."
        )


def pip_command(*arguments):
    return [
        sys.executable,
        "-I",
        "-m",
        "pip",
        "--disable-pip-version-check",
        "--no-color",
        *arguments,
    ]


def run_pip(arguments):
    print("pip " + " ".join(arguments), flush=True)
    completed = subprocess.run(
        pip_command(*arguments),
        stdout=sys.stdout,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=300,
    )
    if completed.returncode:
        raise RuntimeError(
            f"pip wurde mit Fehlercode {completed.returncode} beendet. Bitte die Meldungen im Protokoll prüfen."
        )


def install():
    info = environment()
    ensure_writable_environment(info)
    arguments = [
        "install",
        "--upgrade",
        "--no-cache-dir",
        "--progress-bar",
        "off",
        "--timeout",
        "15",
        "--retries",
        "1",
    ]
    if info["user"]:
        arguments.append("--user")
    run_pip([*arguments, "miniworlds"])
    return inspect_installation()


def repair_candidates(root):
    """Only exact package names in this interpreter's installation scheme.

    A symlink or editable checkout is deliberately never moved. Extensions
    such as miniworlds-data/physics/robot are separate packages.
    """
    root = Path(root)
    if root.is_symlink():
        raise RuntimeError(
            "Das Paketverzeichnis ist verknüpft. Bitte diese Installation manuell prüfen."
        )
    candidates = []
    if not root.exists():
        return candidates
    for path in root.iterdir():
        package = path.name == "miniworlds"
        dist = re.fullmatch(
            r"miniworlds-([0-9][A-Za-z0-9.!+_-]*)\.(dist-info|egg-info)", path.name
        )
        if not package and not dist:
            continue
        if path.is_symlink() or not path.is_dir():
            raise RuntimeError(
                f"{path.name} ist keine normale Paketinstallation. Automatische Reparatur ist hier nicht geeignet."
            )
        if dist:
            for filename in ("METADATA", "PKG-INFO"):
                file = path / filename
                if file.exists():
                    content = file.read_text(encoding="utf-8")
                    name = re.search(r"^Name:\s*(.+)$", content, re.MULTILINE)
                    if name and normalized(name.group(1).strip()) != "miniworlds":
                        raise RuntimeError(
                            "Die Paketinformationen gehören zu einem anderen Paket. Keine Dateien wurden verschoben."
                        )
            direct = path / "direct_url.json"
            if direct.exists() and json.loads(direct.read_text()).get(
                "dir_info", {}
            ).get("editable"):
                raise RuntimeError(
                    "Dies ist eine Entwicklungsinstallation. Bitte den Quellordner und die Installation manuell prüfen."
                )
        # Do not follow links within an otherwise ordinary package either.
        if any(child.is_symlink() for child in path.rglob("*")):
            raise RuntimeError(
                f"{path.name} enthält Verknüpfungen. Keine automatische Bereinigung."
            )
        candidates.append(path)
    return candidates


def valid_wheel(folder):
    wheels = list(Path(folder).glob("miniworlds-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            "Es wurde kein eindeutiges miniworlds-Wheel geladen. Die vorhandene Installation bleibt erhalten."
        )
    with zipfile.ZipFile(wheels[0]) as archive:
        entries = archive.namelist()
        if "miniworlds/__init__.py" not in entries:
            raise RuntimeError(
                "Das heruntergeladene Wheel enthält keine miniworlds-Bibliothek."
            )
    return wheels[0]


def repair(backup_root):
    info = environment()
    ensure_writable_environment(info)
    state = inspect_installation()
    if state["editable"]:
        raise RuntimeError(
            "Eine Entwicklungsinstallation wird nicht automatisch bereinigt."
        )
    root = Path(info["root"]).resolve()
    original = repair_candidates(
        root
    )  # Validate before downloading or moving anything.
    backup_root = Path(backup_root).resolve()
    if backup_root == root or root in backup_root.parents:
        raise RuntimeError("Die Sicherung muss außerhalb von site-packages liegen.")
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix="miniworlds-", dir=backup_root))
    wheels = backup / "download"
    wheels.mkdir()
    print("Sicherung und Protokoll: " + str(backup), flush=True)
    # Obtain all binary distributions first: offline, TLS and resolver failures
    # therefore cannot remove an already working library.
    run_pip(
        [
            "download",
            "--only-binary=:all:",
            "--no-cache-dir",
            "--progress-bar",
            "off",
            "--timeout",
            "15",
            "--retries",
            "1",
            "--dest",
            str(wheels),
            "miniworlds",
        ]
    )
    wheel = valid_wheel(wheels)
    manifest = {
        "time": time.time(),
        "root": str(root),
        "state": "prepared",
        "moves": [],
    }
    manifest_path = backup / "manifest.json"

    def save():
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    save()
    # Copy backups first; never rely on a cross-filesystem move that may
    # partially remove its source before reporting an error.
    for path in original:
        shutil.copytree(path, backup / path.name)
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".miniworlds-repair-", dir=root))
    manifest["staging"] = str(staging)
    save()
    moved = []
    try:
        for path in original:
            destination = staging / path.name
            path.rename(destination)
            moved.append((path, destination))
            manifest["moves"].append(
                {
                    "original": str(path),
                    "backup": str(backup / path.name),
                    "staging": str(destination),
                }
            )
            save()
        manifest["state"] = "installing"
        save()
        arguments = [
            "install",
            "--no-index",
            "--find-links",
            str(wheels),
            "--no-cache-dir",
            "--progress-bar",
            "off",
        ]
        if info["user"]:
            arguments.append("--user")
        # The wheel is explicit: a different system installation must not make
        # pip decide that the requested library is already satisfied.
        run_pip([*arguments, "--force-reinstall", "--no-deps", str(wheel)])
        # Resolve only missing/incompatible dependencies; already satisfied
        # dependencies are left alone by this second, ordinary install.
        run_pip([*arguments, "miniworlds"])
        importlib.invalidate_caches()
        result = inspect_installation()
        if (
            not result["version"]
            or not result["module"]
            or any(
                not issue.startswith("Mehrere miniworlds") for issue in result["issues"]
            )
        ):
            raise RuntimeError(
                "Die neue Installation ist bei der Abschlussprüfung noch unvollständig."
            )
        manifest["state"] = "complete"
        save()
        result["backup"] = str(backup)
        try:
            shutil.rmtree(staging)
        except OSError:
            print(
                "Die alte Installation liegt zusätzlich unter " + str(staging),
                flush=True,
            )
        return result
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        # Keep the failed attempt for diagnosis, then restore the original
        # package and metadata without touching any unrelated package.
        failed = staging / "failed-installation"
        failed.mkdir(exist_ok=True)
        saved_names = {path.name for path, _ in moved}
        for path in repair_candidates(root):
            if path.name in saved_names or path not in original:
                path.rename(failed / path.name)
        for path, destination in reversed(moved):
            destination.rename(path)
        manifest["state"] = "restored"
        save()
        try:
            shutil.copytree(failed, backup / "failed-installation")
            shutil.rmtree(staging)
        except OSError:
            print(
                "Fehlversuch zusätzlich gespeichert unter " + str(staging), flush=True
            )
        print(
            "Die bisherige miniworlds-Installation wurde wiederhergestellt. Sicherung: "
            + str(backup),
            flush=True,
        )
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("inspect", "install", "repair"))
    parser.add_argument("--backup-root")
    args = parser.parse_args()
    try:
        if args.action == "inspect":
            result = inspect_installation()
        elif args.action == "install":
            result = install()
        elif args.backup_root:
            result = repair(args.backup_root)
        else:
            raise ValueError("Für die Reparatur fehlt der Sicherungsordner.")
        result["ok"] = True
    except (
        OSError,
        RuntimeError,
        ValueError,
        subprocess.SubprocessError,
        zipfile.BadZipFile,
    ) as error:
        result = {"ok": False, "error": str(error)}
    print(RESULT_PREFIX + json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
