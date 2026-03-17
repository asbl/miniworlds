import unittest

from miniworlds.tools import method_caller


class Receiver:
    def __init__(self):
        self.calls = []

    def receive(self, value):
        self.calls.append(value)

    def ping(self):
        self.calls.append("ping")


class TestMethodCaller(unittest.TestCase):
    def test_call_method_handles_arguments_and_none(self):
        receiver = Receiver()

        method_caller.call_method(receiver.receive, ["value"])
        method_caller.call_method(receiver.ping, None)

        self.assertEqual(receiver.calls, ["value", "ping"])

    def test_signature_cache_records_hits_for_repeated_calls(self):
        receiver = Receiver()
        method = receiver.receive
        method_caller._cached_signature.cache_clear()

        for _ in range(5):
            method_caller.call_method(method, ["value"])

        cache_info = method_caller._cached_signature.cache_info()

        self.assertGreater(cache_info.hits, 0)


if __name__ == "__main__":
    unittest.main()