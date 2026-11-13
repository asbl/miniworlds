"""Read PyPI's public index; failures never imply that a library is current."""

import json
import urllib.request

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.utils import (
    InvalidSdistFilename,
    InvalidWheelFilename,
    parse_sdist_filename,
    parse_wheel_filename,
)
from packaging.version import InvalidVersion, Version


def release_versions(data, python):
    available, compatible = set(), set()
    for entry in data.get("files", []):
        if entry.get("yanked"):
            continue
        filename = entry.get("filename", "")
        try:
            if filename.endswith(".whl"):
                name, version, _, _ = parse_wheel_filename(filename)
            else:
                name, version = parse_sdist_filename(filename)
            if (
                str(name) != "miniworlds"
                or version.is_prerelease
                or version.is_devrelease
            ):
                continue
            required = SpecifierSet(entry.get("requires-python") or "")
            available.add(version)
            if required.contains(python, prereleases=True):
                compatible.add(version)
        except (
            InvalidVersion,
            InvalidSpecifier,
            InvalidWheelFilename,
            InvalidSdistFilename,
        ):
            continue
    if not available:
        raise ValueError("PyPI meldet keine reguläre miniworlds-Version.")
    return {
        "latest": str(max(available)),
        "compatible": str(max(compatible)) if compatible else None,
    }


def fetch_versions(python):
    request = urllib.request.Request(
        "https://pypi.org/simple/miniworlds/",
        headers={
            "Accept": "application/vnd.pypi.simple.v1+json",
            "User-Agent": "thonny-miniworlds update-check",
        },
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Die Versionsantwort von PyPI ist unerwartet groß.")
    return release_versions(json.loads(raw), python)


def version_message(installed, versions):
    if versions.get("error"):
        return (
            "Online-Prüfung nicht möglich: "
            + versions["error"]
            + "\nOb ein Update verfügbar ist, konnte nicht festgestellt werden."
        )
    latest, compatible = versions["latest"], versions["compatible"]
    message = f"Neueste Version auf PyPI: {latest}\n"
    if compatible is None:
        return (
            message
            + "Für diesen Python-Interpreter wurde keine passende reguläre Version gefunden."
        )
    if compatible != latest:
        message += f"Passend zu deinem Python: {compatible}. Für die neueste Version ist eine andere Python-Version nötig.\n"
    if installed is None:
        return message + "miniworlds ist noch nicht installiert."
    try:
        current, target = Version(installed), Version(compatible)
    except InvalidVersion:
        return (
            message
            + "Die installierte Versionsangabe ist nicht lesbar; bitte die Installation prüfen."
        )
    if current < target:
        return message + f"Update verfügbar: {installed} → {compatible}"
    if current > target:
        return (
            message
            + f"Installiert ist eine neuere oder Entwicklungsversion ({installed})."
        )
    return message + "Deine miniworlds-Version ist aktuell."


def installation_hint(log):
    lower = log.lower()
    if "externally-managed" in lower or "pep 668" in lower:
        return "Diese Python-Umgebung wird vom Betriebssystem verwaltet. Wähle eine virtuelle Umgebung; eine Bereinigung der Paketdateien löst das nicht."
    if any(
        word in lower
        for word in (
            "record file not found",
            "uninstall-no-record",
            "cannot uninstall",
            "invalid distribution",
            "metadata",
        )
    ):
        return "Paketinformationen können beschädigt sein. Versuche „Reparieren mit Sicherung“."
    if any(
        word in lower
        for word in (
            "permission denied",
            "access is denied",
            "winerror 5",
            "winerror 32",
            "being used by another process",
        )
    ):
        return "Dateien sind gesperrt oder nicht beschreibbar. Schließe andere laufende Python-Programme und prüfe die Rechte für die ausgewählte venv."
    if any(
        word in lower
        for word in (
            "ssl",
            "certificate",
            "connection",
            "timed out",
            "proxyerror",
            "network",
            "name resolution",
        )
    ):
        return "Die Verbindung zum Paketserver ist fehlgeschlagen. Prüfe Schulnetz, Proxy und Zertifikate; Paketdateien müssen dafür nicht gelöscht werden."
    if "no module named pip" in lower:
        return "pip fehlt im ausgewählten Interpreter. Lege eine virtuelle Umgebung mit pip an."
    if any(
        word in lower
        for word in (
            "no matching distribution",
            "requires a different python",
            "could not find a version",
        )
    ):
        return "Für diesen Interpreter wurde kein passendes Paket gefunden. Prüfe Python-Version und den Paketserver deiner Schule."
    return "Die Installation ist fehlgeschlagen. Im Protokoll steht die Ursache. Bei unvollständigen miniworlds-Dateien kann „Reparieren mit Sicherung“ helfen."
