"""Real loopback routing, origin and method security by Jason Stys. Index: docs/CODE_INDEX.md."""

import http.client
import json
import threading
from contextlib import closing

import pytest

from sensorlab.server import make_server


@pytest.fixture
def service(tmp_path):
    """Start a real loopback service with minimal built assets and always stop its own thread."""
    (tmp_path / "index.html").write_text("<html>DATUM</html>", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/app.js").write_text("// owned test asset", encoding="utf-8")
    with make_server(tmp_path) as server:
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join(timeout=5)


def request(server, path, method="GET", headers=None):
    """Return status/headers/body from a closed HTTP connection, including rejection paths."""
    with closing(
        http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=15)
    ) as connection:
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/assets/app.js",
        "/api/health",
        "/api/catalog",
        "/api/run",
        "/api/report?format=json",
        "/api/report?format=csv",
        "/api/report?format=html",
        "/api/report?format=input",
    ],
)
def test_success(service, path):
    """Every supported route has restrictive headers, and reports are attachment-only."""
    status, headers, body = request(service, path)
    assert status == 200 and body
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in headers["Content-Security-Policy"]
    assert headers["Cache-Control"] == "no-store"
    assert "Access-Control-Allow-Origin" not in headers
    assert ("Content-Disposition" in headers) == path.startswith("/api/report")
    if path == "/api/run":
        assert json.loads(body)["verification"]["native_reference_verified"]


@pytest.mark.parametrize(
    "path,status",
    [
        ("/api/run?limit=9", 400),
        ("/api/run?limit=yes", 400),
        ("/api/run?x=1", 400),
        ("/api/run?limit=2&limit=3", 400),
        ("/api/run?format=json", 400),
        ("/api/report?format=exe", 400),
        ("/api/run?" + "&".join(f"a{i}=1" for i in range(9)), 400),
        ("/" + "x" * 1025, 414),
        ("/../LICENSE", 404),
        ("/%2e%2e/LICENSE", 404),
        ("/assets/../../LICENSE", 404),
        ("/assets/a.py", 404),
        ("/assets/missing.js", 404),
        ("/.env", 404),
        ("/?x=1", 404),
        ("/api/health?x=1", 404),
    ],
)
def test_rejections(service, path, status):
    """Bounded queries, finite settings and confined static routes fail closed."""
    assert request(service, path)[0] == status


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "evil.example"},
        {"Origin": "https://evil.example"},
        {"Sec-Fetch-Site": "cross-site"},
    ],
)
def test_origins(service, headers):
    """Reject DNS rebinding, cross-origin scripts and cross-site browser requests."""
    assert request(service, "/api/run", headers=headers)[0] == 403


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
def test_mutation(service, method):
    """The website has no upload, hardware control or database mutation surface."""
    assert request(service, "/api/run", method)[0] == 405


def test_resource_failure(service, monkeypatch):
    """Internal verification failure yields a generic error and no partial verified evidence."""

    def fail(settings):
        """Inject a model failure without exposing a traceback or local path to the browser."""
        raise RuntimeError("private detail")

    monkeypatch.setattr("sensorlab.server.build_run", fail)
    status, _, body = request(service, "/api/run")
    assert status == 500 and b"private detail" not in body
