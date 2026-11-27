#!/usr/bin/env python
# coding:utf-8

import hashlib
import io

from meshroom.core import httpUtils


class FakeResponse(io.BytesIO):
    """ A response of urllib.request.urlopen(), served from memory. """

    def __init__(self, body, status, headers):
        super().__init__(body)
        self.status = status
        self.headers = headers


def test_fetchToFileResumesInterruptedDownload(tmp_path, monkeypatch):
    """ A download cut by the server is resumed from the received bytes, with a range request. """
    content = b"0123456789"
    requests = []

    def urlopen(request, timeout):
        requests.append(request)
        if not request.has_header("Range"):
            # The connection is closed after half of the content.
            return FakeResponse(content[:5], 200, {"Content-Length": "10", "ETag": '"v1"'})
        assert request.get_header("Range") == "bytes=5-" and request.get_header("If-range") == '"v1"'
        return FakeResponse(content[5:], 206, {"Content-Range": "bytes 5-9/10", "ETag": '"v1"'})

    monkeypatch.setattr(httpUtils.urllib.request, "urlopen", urlopen)
    sha256 = httpUtils.fetchToFile("https://example.org/file.bin", tmp_path / "file.bin")

    assert len(requests) == 2
    assert (tmp_path / "file.bin").read_bytes() == content
    assert sha256 == hashlib.sha256(content).hexdigest()
