"""Frontend-only socket transport. Never imports the game engine."""

import hmac
import json
import queue
import secrets
import socket
import threading


class Connection:
    def __init__(self):
        self.events = queue.Queue()
        self.token = secrets.token_hex(32)
        self.generation = None
        self.closed = False
        self.sequence = 0
        self.socket = None
        self.writer = None
        self.server = socket.socket()
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(4)
        self.server.settimeout(0.5)
        self.port = self.server.getsockname()[1]
        self.thread = threading.Thread(target=self._receive, daemon=True)
        self.thread.start()

    def _receive(self):
        try:
            while not self.closed:
                try:
                    client, _ = self.server.accept()
                except TimeoutError:
                    continue
                client.settimeout(5)
                stream = client.makefile("r", encoding="utf-8")
                try:
                    first = json.loads(stream.readline(4096))
                    if not isinstance(first, dict) or not isinstance(
                        first.get("generation"), str
                    ):
                        raise TypeError("Invalid experiment handshake")
                    if not hmac.compare_digest(str(first.get("token", "")), self.token):
                        raise ValueError("Invalid experiment token")
                except (TypeError, ValueError, OSError):
                    stream.close()
                    client.close()
                    continue
                self.socket = client
                self.generation = first["generation"]
                self.writer = client.makefile("w", encoding="utf-8")
                client.settimeout(None)
                self.server.close()
                for line in stream:
                    response = json.loads(line)
                    if response.get("generation") == self.generation:
                        self.events.put(response)
                stream.close()
                break
        except (OSError, ValueError) as error:
            if not self.closed:
                self.events.put({"ok": False, "error": str(error)})
        finally:
            self.events.put({"ended": True})

    def send(self, command):
        if self.closed or self.writer is None:
            raise OSError("Keine Verbindung zur Experimentiersitzung")
        self.sequence += 1
        command = dict(command, id=self.sequence, generation=self.generation)
        self.writer.write(json.dumps(command, ensure_ascii=False) + "\n")
        self.writer.flush()
        return self.sequence

    def close(self):
        self.closed = True
        self.server.close()
        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.socket.close()
        if self.writer is not None:
            try:
                self.writer.close()
            except OSError:
                pass
