"""Lifecycle contract of the optional engine host, without changing normal runs."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from miniworlds.base import runtime_host

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def clean_host():
    runtime_host.stop(None)
    yield
    runtime_host.stop(None)


def test_no_host_is_noop():
    assert runtime_host.API_VERSION == 1
    runtime_host.start(None)
    runtime_host.poll(None)
    runtime_host.stop(None)


def test_start_poll_and_idempotent_stop():
    host = SimpleNamespace(start=Mock(), poll=Mock(), close=Mock())
    app = object()
    runtime_host.install(host)
    runtime_host.start(app)
    runtime_host.poll(app)
    runtime_host.stop(app)
    runtime_host.stop(app)
    host.start.assert_called_once_with(app)
    host.poll.assert_called_once_with(app)
    host.close.assert_called_once()


def test_failed_replacement_does_not_leave_closed_host_installed():
    old = SimpleNamespace(
        close=Mock(side_effect=RuntimeError("close failed")), poll=Mock()
    )
    runtime_host.install(old)
    with pytest.raises(RuntimeError, match="close failed"):
        runtime_host.install(object())
    runtime_host.poll(None)
    old.poll.assert_not_called()
