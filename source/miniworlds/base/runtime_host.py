"""Internal, opt-in IDE integration. No host is installed in ordinary programs."""

API_VERSION = 1

_host = None


def install(host):
    global _host
    previous, _host = _host, None
    if previous is not None:
        previous.close()
    _host = host


def start(app):
    if _host is not None:
        _host.start(app)


def poll(app):
    if _host is not None:
        _host.poll(app)


def stop(app):
    global _host
    host, _host = _host, None
    if host is not None:
        host.close()
