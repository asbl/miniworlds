import time

from miniworlds.tools import method_caller
from logic_benchmark_utils import record_measurement_summary


class Receiver:
    def receive(self, value):
        return value


def profile_method_caller(iterations: int = 50000):
    receiver = Receiver()
    method = receiver.receive
    method_caller._cached_signature.cache_clear()

    start = time.perf_counter()
    for _ in range(iterations):
        method_caller.call_method(method, ["payload"])
    first_pass = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iterations):
        method_caller.call_method(method, ["payload"])
    second_pass = time.perf_counter() - start

    cache_info = method_caller._cached_signature.cache_info()
    print(
        f"method caller: first {iterations} calls in {first_pass * 1000:.2f} ms, "
        f"second pass in {second_pass * 1000:.2f} ms"
    )
    print(f"method caller cache: hits={cache_info.hits}, misses={cache_info.misses}")
    record_measurement_summary(
        "method caller",
        {
            "iterations": iterations,
            "first_pass_ms": round(first_pass * 1000, 4),
            "second_pass_ms": round(second_pass * 1000, 4),
            "cache_hits": cache_info.hits,
            "cache_misses": cache_info.misses,
        },
    )


if __name__ == "__main__":
    profile_method_caller()