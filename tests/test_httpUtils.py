import hashlib
import threading

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from meshroom.core.httpUtils import RequestError, _contentValidator, fetchToFile, fetchWithProgress

CONTENT = bytes(range(256)) * 1024
ETAG = '"content-v1"'


class Server:
    """
    A local HTTP server serving "CONTENT", whose behavior for each request is taken from "behaviors":
        - "full": the whole content.
        - "truncated": announce the whole content, but close the connection halfway.
        - "range": the requested range (HTTP 206), or the whole content without a "Range" header.
        - "partial": the first half of the requested range (HTTP 206).
        - "unidentified": like "truncated", without anything identifying the content.
        - "changed": the requested range of a new version of the content, ignoring its "If-Range" header.
        - "notFound": an HTTP 404 error.
    The last behavior is repeated for any further request. "requests" stores the "Range" header of each request,
    and "validators" its "If-Range" header.
    """
    def __init__(self, behaviors):
        self.behaviors = list(behaviors)
        self.requests = []
        self.validators = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                rangeHeader = self.headers.get("Range")
                server.requests.append(rangeHeader)
                server.validators.append(self.headers.get("If-Range"))
                behavior = server.behaviors.pop(0) if len(server.behaviors) > 1 else server.behaviors[0]
                if behavior == "notFound":
                    self.send_error(404)
                    return
                resumes = behavior in ("range", "partial", "changed") and rangeHeader
                start = int(rangeHeader[len("bytes="):-1]) if resumes else 0
                body = CONTENT[start:]
                if start and behavior == "partial":
                    body = body[:len(body) // 2]
                self.send_response(206 if start else 200)
                if start:
                    self.send_header("Content-Range", f"bytes {start}-{start + len(body) - 1}/{len(CONTENT)}")
                if behavior != "unidentified":
                    self.send_header("ETag", '"content-v2"' if behavior == "changed" else ETAG)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body[:len(body) // 2] if behavior in ("truncated", "unidentified") else body)

            def log_message(self, *args):
                pass

        self._httpServer = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._httpServer.server_address[1]}/asset.bin"
        threading.Thread(target=self._httpServer.serve_forever, daemon=True).start()

    def close(self):
        self._httpServer.shutdown()
        self._httpServer.server_close()


@pytest.fixture
def server(request):
    instance = Server(request.param)
    yield instance
    instance.close()


@pytest.mark.parametrize("server", [["full"]], indirect=True)
def test_fetchToFile(server, tmp_path):
    destination = tmp_path / "asset.bin"
    digest = fetchToFile(server.url, destination)
    assert destination.read_bytes() == CONTENT
    assert digest == hashlib.sha256(CONTENT).hexdigest()
    assert server.requests == [None]


@pytest.mark.parametrize("server", [["truncated"]], indirect=True)
def test_fetchToFileIncomplete(server, tmp_path):
    destination = tmp_path / "asset.bin"
    with pytest.raises(RequestError, match="Incomplete download"):
        fetchToFile(server.url, destination)
    # Every attempt is made, and no partial file is left behind.
    assert len(server.requests) == 3
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("server", [["truncated", "range"]], indirect=True)
def test_fetchToFileResumed(server, tmp_path):
    destination = tmp_path / "asset.bin"
    progress = []
    digest = fetchToFile(server.url, destination, onBytes=lambda bytesRead, total: progress.append((bytesRead, total)))
    assert destination.read_bytes() == CONTENT
    assert digest == hashlib.sha256(CONTENT).hexdigest()
    # The second request asks for the missing bytes only, of the same content.
    assert server.requests == [None, f"bytes={len(CONTENT) // 2}-"]
    assert server.validators == [None, ETAG]
    # The progress is the one of the whole content.
    assert progress[-1] == (len(CONTENT), len(CONTENT))
    assert all(total == len(CONTENT) for _, total in progress)


@pytest.mark.parametrize("server", [["truncated", "full"]], indirect=True)
def test_fetchToFileRestarted(server, tmp_path):
    # A server ignoring the "Range" header sends the whole content again.
    destination = tmp_path / "asset.bin"
    digest = fetchToFile(server.url, destination)
    assert destination.read_bytes() == CONTENT
    assert digest == hashlib.sha256(CONTENT).hexdigest()
    assert len(server.requests) == 2


@pytest.mark.parametrize("server", [["truncated", "partial", "range"]], indirect=True)
def test_fetchToFileResumedPartially(server, tmp_path):
    # A resumed response holding a part of what is missing is not the end of the content.
    destination = tmp_path / "asset.bin"
    digest = fetchToFile(server.url, destination)
    assert destination.read_bytes() == CONTENT
    assert digest == hashlib.sha256(CONTENT).hexdigest()
    half = len(CONTENT) // 2
    assert server.requests == [None, f"bytes={half}-", f"bytes={half + half // 2}-"]


@pytest.mark.parametrize("server", [["truncated", "partial"]], indirect=True)
def test_fetchToFileResumedPartiallyIncomplete(server, tmp_path):
    # The content is never complete: no partial file is published.
    destination = tmp_path / "asset.bin"
    with pytest.raises(RequestError, match="Incomplete download"):
        fetchToFile(server.url, destination)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("server", [["unidentified", "full"]], indirect=True)
def test_fetchToFileNotResumedWithoutValidator(server, tmp_path):
    # Nothing tells that the content is the same: its rest is not appended, it is downloaded again.
    destination = tmp_path / "asset.bin"
    digest = fetchToFile(server.url, destination)
    assert destination.read_bytes() == CONTENT
    assert digest == hashlib.sha256(CONTENT).hexdigest()
    assert server.requests == [None, None]


@pytest.mark.parametrize("server", [["truncated", "changed", "full"]], indirect=True)
def test_fetchToFileContentChanged(server, tmp_path):
    # The rest of a new version is not appended to the old one, even if the server ignores "If-Range".
    destination = tmp_path / "asset.bin"
    digest = fetchToFile(server.url, destination)
    assert destination.read_bytes() == CONTENT
    assert digest == hashlib.sha256(CONTENT).hexdigest()
    assert server.requests == [None, f"bytes={len(CONTENT) // 2}-", None]


@pytest.mark.parametrize("headers, expected", [
    ({"ETag": '"abc"'}, '"abc"'),
    ({"ETag": '"abc"', "Last-Modified": "date"}, '"abc"'),
    ({"ETag": 'W/"abc"', "Last-Modified": "date"}, "date"),
    ({"ETag": 'W/"abc"'}, None),
    ({}, None),
])
def test_contentValidator(headers, expected):
    assert _contentValidator(SimpleNamespace(headers=headers)) == expected


@pytest.mark.parametrize("server", [["notFound"]], indirect=True)
def test_fetchToFileHttpError(server, tmp_path):
    # An HTTP error is not attempted again.
    with pytest.raises(RequestError) as excInfo:
        fetchToFile(server.url, tmp_path / "asset.bin")
    assert excInfo.value.code == 404
    assert len(server.requests) == 1


@pytest.mark.parametrize("server", [["truncated"]], indirect=True)
def test_fetchWithProgressIncomplete(server):
    with pytest.raises(RequestError, match="Incomplete download"):
        fetchWithProgress(server.url)
