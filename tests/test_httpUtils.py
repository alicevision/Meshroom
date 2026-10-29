import hashlib
import threading

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from meshroom.core.httpUtils import RequestError, fetchToFile, fetchWithProgress

CONTENT = bytes(range(256)) * 1024


class Server:
    """
    A local HTTP server serving "CONTENT", whose behavior for each request is taken from "behaviors":
        - "full": the whole content.
        - "truncated": announce the whole content, but close the connection halfway.
        - "range": the requested range (HTTP 206), or the whole content without a "Range" header.
        - "notFound": an HTTP 404 error.
    The last behavior is repeated for any further request. "requests" stores the "Range" header of each request.
    """
    def __init__(self, behaviors):
        self.behaviors = list(behaviors)
        self.requests = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                rangeHeader = self.headers.get("Range")
                server.requests.append(rangeHeader)
                behavior = server.behaviors.pop(0) if len(server.behaviors) > 1 else server.behaviors[0]
                if behavior == "notFound":
                    self.send_error(404)
                    return
                start = int(rangeHeader[len("bytes="):-1]) if behavior == "range" and rangeHeader else 0
                body = CONTENT[start:]
                self.send_response(206 if start else 200)
                if start:
                    self.send_header("Content-Range", f"bytes {start}-{len(CONTENT) - 1}/{len(CONTENT)}")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body[:len(body) // 2] if behavior == "truncated" else body)

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
    # The second request asks for the missing bytes only.
    assert server.requests == [None, f"bytes={len(CONTENT) // 2}-"]
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
