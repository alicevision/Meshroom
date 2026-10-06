from __future__ import annotations

import http.client
import urllib.error
import urllib.request

from typing import Callable, Optional
from contextlib import contextmanager

# Timeout (in seconds) for network download requests.
_HTTP_REQUEST_TIMEOUT = 10
# Chunk size (in bytes) used when streaming a download to report progress.
_HTTP_CHUNK_SIZE = 64 * 1024
# Network failures that urllib does not always wrap in a URLError (e.g. TimeoutError).
_HTTP_NETWORK_ERRORS = (OSError, http.client.HTTPException)


class RequestError(Exception):
    """
    Raised when a request fails.
    "code" is the HTTP status for an HTTPError, or None.
    """
    def __init__(self, message: str, code: Optional[int] = None):
        super().__init__(message)
        self.code = code


@contextmanager
def _open(url: str, timeout: float):
    """
    Open "url", translating urllib's network/HTTP errors into RequestError.

    Args:
        url: the url to open.
        timeout: the timeout (in seconds) of the request.

    Yields:
        The open response, as returned by urllib.request.urlopen().

    Raises:
        RequestError: if the request fails.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            yield response
    except urllib.error.HTTPError as exc:
        raise RequestError(str(exc), code=exc.code) from exc
    except _HTTP_NETWORK_ERRORS as exc:
        raise RequestError(f"{type(exc).__name__}: {exc}") from exc


def _contentLength(response) -> int:
    """
    Return the "Content-Length" of "response", or -1 if it is missing or invalid.

    Args:
        response: the open response, as returned by urllib.request.urlopen().

    Returns:
        int: the size (in bytes) of the response's body, or -1 if unknown.
    """
    contentLength = response.headers.get("Content-Length")
    if contentLength is None:
        return -1
    try:
        return int(contentLength)
    except ValueError:
        return -1


def readWithProgress(response, onBytes: Optional[Callable[[int, int], None]]) -> bytes:
    """
    Read "response" fully in fixed-size chunks, returning the concatenated content.

    Args:
        response: the open response, as returned by urllib.request.urlopen().
        onBytes: if provided, called after each chunk with "(bytesRead, totalBytes)", "totalBytes"
                 being -1 if unknown.

    Returns:
        bytes: the content of the response.
    """
    total = _contentLength(response)
    chunks = []
    bytesRead = 0
    while True:
        chunk = response.read(_HTTP_CHUNK_SIZE)
        if not chunk:
            break
        chunks.append(chunk)
        bytesRead += len(chunk)
        if onBytes:
            onBytes(bytesRead, total)
    return b"".join(chunks)


def etagMatch(url: str, etag: str) -> bool:
    """
    Check whether "url"'s remote content still matches "etag", using a conditional GET with an
    "If-None-Match" header, without downloading the body.

    Args:
        url: the url to check.
        etag: the ETag of the content previously downloaded from "url".

    Returns:
        bool: True if the server confirmed the content still matches (HTTP 304), False if it
        changed, or on any request failure.
    """
    request = urllib.request.Request(url, headers={"If-None-Match": etag})
    try:
        urllib.request.urlopen(request, timeout=_HTTP_REQUEST_TIMEOUT)
        return False
    except urllib.error.HTTPError as exc:
        return exc.code == 304
    except _HTTP_NETWORK_ERRORS:
        return False


def fetchStatus(url: str, method: str = "GET", timeout: float = _HTTP_REQUEST_TIMEOUT) -> Optional[int]:
    """
    Open "url" without reading its body and return the resulting HTTP status code, or None.

    Args:
        url: the url to open.
        method: the HTTP method of the request (e.g. "GET", "HEAD").
        timeout: the timeout (in seconds) of the request.

    Returns:
        int | None: the HTTP status code, or None if the request failed without one (e.g. network error).
    """
    request = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except _HTTP_NETWORK_ERRORS:
        return None


def fetch(url: str, timeout: float = _HTTP_REQUEST_TIMEOUT) -> bytes:
    """
    GET "url" fully.

    Args:
        url: the url to download.
        timeout: the timeout (in seconds) of the request.

    Returns:
        bytes: the downloaded content.

    Raises:
        RequestError: if the request fails.
    """
    with _open(url, timeout) as response:
        return response.read()


def fetchWithETag(url: str, timeout: float = _HTTP_REQUEST_TIMEOUT) -> tuple[bytes, Optional[str]]:
    """
    GET "url" fully with Etag.

    Args:
        url: the url to download.
        timeout: the timeout (in seconds) of the request.

    Returns:
        tuple[bytes, str | None]: the downloaded content and the response's ETag header (if any).

    Raises:
        RequestError: if the request fails.
    """
    with _open(url, timeout) as response:
        return response.read(), response.headers.get("ETag")


def fetchWithProgress(url: str, onBytes: Optional[Callable[[int, int], None]] = None,
                      timeout: float = _HTTP_REQUEST_TIMEOUT) -> bytes:
    """
    GET "url" fully, reporting progress via "onBytes" as the body streams in.

    Args:
        url: the url to download.
        onBytes: if provided, called after each chunk with "(bytesRead, totalBytes)", "totalBytes"
                 being -1 if unknown.
        timeout: the timeout (in seconds) of the request.

    Returns:
        bytes: the downloaded content.

    Raises:
        RequestError: if the request fails.
    """
    with _open(url, timeout) as response:
        return readWithProgress(response, onBytes)
