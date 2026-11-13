import importlib
import json
import socket
import sys
from types import ModuleType

from test.unittests.thonny_plugin.test_learning_tools import ROOT

package = ModuleType("_live_transport_tests")
package.__path__ = [str(ROOT / "libraries/thonny-miniworlds/thonnycontrib/miniworlds")]
sys.modules[package.__name__] = package
Connection = importlib.import_module(package.__name__ + ".live_connection").Connection


def test_authentication_correlation_and_generation_filter():
    connection = Connection()
    wrong = socket.create_connection(("127.0.0.1", connection.port))
    wrong.sendall(b'{"token":"wrong"}\n')
    wrong.close()
    client = socket.create_connection(("127.0.0.1", connection.port))
    stream = client.makefile("rw", encoding="utf-8")
    try:
        stream.write(
            json.dumps({"token": connection.token, "generation": "new"}) + "\n"
        )
        stream.write(json.dumps({"ok": True, "generation": "old"}) + "\n")
        stream.write(json.dumps({"ok": True, "generation": "new", "data": {}}) + "\n")
        stream.flush()
        assert connection.events.get(timeout=5)["generation"] == "new"
        request = connection.send({"action": "inspect"})
        command = json.loads(stream.readline())
        assert command["id"] == request and command["generation"] == "new"
        connection.close()
        assert connection.thread.is_alive() or connection.closed
    finally:
        connection.close()
        stream.close()
        client.close()
        connection.thread.join(timeout=2)
    assert not connection.thread.is_alive()
