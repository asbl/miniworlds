"""Build and run the miniworlds Pyodide suite in headless Chromium."""

from __future__ import annotations

import argparse
import base64
import functools
import http.server
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import quote
from urllib.request import urlopen
import zipfile


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        del format, args


def build_wheel(target: Path) -> str:
    subprocess.run(
        [
            sys.executable,
            "setup.py",
            "bdist_wheel",
            "--dist-dir",
            str(target),
            "--bdist-dir",
            str(target / "build"),
        ],
        cwd=ROOT / "source",
        check=True,
        stdout=subprocess.DEVNULL,
    )
    wheels = list(target.glob("miniworlds-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected one miniworlds wheel, found {len(wheels)}")
    return wheels[0].name


def build_student_project(target: Path) -> None:
    project = target / "project"
    shutil.copytree(HERE / "project", project)
    shutil.copy2(ROOT / "test/visualtests/images/player.png", project / "images/player.png")
    shutil.copy2(ROOT / "test/visualtests/images/ball.png", project / "images/ball.png")
    with zipfile.ZipFile(target / "project.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in project.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                archive.write(path, path.relative_to(project))


def find_chromium(explicit: str | None) -> str:
    candidates = [explicit, "chromium", "chromium-browser", "google-chrome"]
    for candidate in candidates:
        if candidate and shutil.which(candidate):
            return shutil.which(candidate) or candidate
    raise RuntimeError("Chromium not found. Set --chromium or MINIWORLDS_CHROMIUM.")


class DevToolsClient:
    def __init__(self, websocket_url: str):
        host_port, path = websocket_url.removeprefix("ws://").split("/", 1)
        host, port = host_port.split(":")
        self.socket = socket.create_connection((host, int(port)), timeout=60)
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        request = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.socket.sendall(request.encode())
        response = self.socket.recv(4096)
        if b" 101 " not in response:
            raise RuntimeError("Could not connect to Chromium DevTools")
        self.next_id = 1

    def _send(self, payload: dict) -> None:
        data = json.dumps(payload).encode()
        mask = secrets.token_bytes(4)
        length = len(data)
        if length < 126:
            header = bytes([0x81, 0x80 | length])
        elif length < 65536:
            header = bytes([0x81, 0x80 | 126]) + length.to_bytes(2, "big")
        else:
            header = bytes([0x81, 0x80 | 127]) + length.to_bytes(8, "big")
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(data))
        self.socket.sendall(header + mask + masked)

    def _receive(self) -> dict:
        header = self.socket.recv(2)
        if len(header) != 2:
            raise RuntimeError("Chromium DevTools connection closed")
        length = header[1] & 0x7F
        if length == 126:
            length = int.from_bytes(self.socket.recv(2), "big")
        elif length == 127:
            length = int.from_bytes(self.socket.recv(8), "big")
        chunks = []
        remaining = length
        while remaining:
            chunk = self.socket.recv(remaining)
            if not chunk:
                raise RuntimeError("Chromium DevTools connection closed")
            chunks.append(chunk)
            remaining -= len(chunk)
        return json.loads(b"".join(chunks))

    def call(self, method: str, params: dict | None = None) -> dict:
        message_id = self.next_id
        self.next_id += 1
        self._send({"id": message_id, "method": method, "params": params or {}})
        while True:
            response = self._receive()
            if response.get("id") == message_id:
                return response

    def close(self) -> None:
        self.socket.close()


def wait_for_devtools_page(port: int, runner_url: str, timeout: int) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with urlopen(f"http://127.0.0.1:{port}/json", timeout=5) as response:
            targets = json.load(response)
        for target in targets:
            if target.get("url", "").startswith(runner_url):
                return target["webSocketDebuggerUrl"]
        time.sleep(0.1)
    raise TimeoutError("Chromium did not open the Pyodide runner page")


def wait_for_result(client: DevToolsClient, timeout: int) -> dict:
    deadline = time.monotonic() + timeout
    last_progress = "page loading"
    while time.monotonic() < deadline:
        response = client.call(
            "Runtime.evaluate",
            {
                "expression": """({
                    result: window.pyodideTestResult || null,
                    progress: window.pyodideTestProgress || "page loading"
                })""",
                "returnByValue": True,
            },
        )
        value = response.get("result", {}).get("result", {}).get("value")
        if value:
            last_progress = value["progress"]
            if value["result"]:
                return value["result"]
        time.sleep(0.1)
    raise TimeoutError(
        f"Pyodide tests did not finish before the timeout; last stage: {last_progress}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromium")
    parser.add_argument("--pyodide-base")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--performance", action="store_true")
    args = parser.parse_args()

    chromium = find_chromium(args.chromium or os.environ.get("MINIWORLDS_CHROMIUM"))
    pyodide_base = args.pyodide_base or os.environ.get("MINIWORLDS_PYODIDE_BASE")
    with tempfile.TemporaryDirectory(prefix="miniworlds-pyodide-") as temp_name:
        temp = Path(temp_name)
        suite_name = "performance_suite.py" if args.performance else "suite.py"
        shutil.copy2(HERE / suite_name, temp / "suite.py")
        wheel_name = build_wheel(temp)
        build_student_project(temp)
        runner_html = (HERE / "runner.html").read_text(encoding="utf-8")
        (temp / "runner.html").write_text(
            runner_html.replace("__MINIWORLDS_WHEEL__", wheel_name),
            encoding="utf-8",
        )

        handler = functools.partial(QuietHandler, directory=temp)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/runner.html"
            if pyodide_base:
                url += f"?pyodide-base={quote(pyodide_base, safe=':/')}"
            browser = subprocess.Popen(
                [
                    chromium,
                    "--headless",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--remote-debugging-port=0",
                    f"--user-data-dir={temp / 'chromium-profile'}",
                    url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            assert browser.stderr is not None
            deadline = time.monotonic() + 20
            devtools_port = None
            while time.monotonic() < deadline:
                line = browser.stderr.readline()
                if "DevTools listening on ws://127.0.0.1:" in line:
                    devtools_port = int(line.split("ws://127.0.0.1:", 1)[1].split("/", 1)[0])
                    break
            if devtools_port is None:
                raise RuntimeError("Chromium did not start its DevTools endpoint")
            websocket_url = wait_for_devtools_page(devtools_port, url, 20)
            client = DevToolsClient(websocket_url)
            try:
                result = wait_for_result(client, args.timeout)
            finally:
                client.close()
                browser.terminate()
                browser.wait(timeout=10)
        finally:
            server.shutdown()
            thread.join()

    for test in result.get("results", []):
        print(f"{test['status'].upper():6} {test['name']}")
        if test["status"] == "failed":
            print(test["traceback"])
    for measurement in result.get("measurements", []):
        details = " ".join(
            f"{key}={value}" for key, value in measurement.items() if key != "name"
        )
        print(f"MEASURE {measurement['name']}: {details}")
    if result.get("error"):
        print(result["error"])
    print(f"{result.get('passed', 0)} passed, {result.get('failed', 0)} failed")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
