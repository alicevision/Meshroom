import hashlib
import http.client
import logging
import re
import urllib.error
import urllib.request

from typing import Callable, Iterator, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager

from meshroom.core.files import atomicOpen

# Timeout (in seconds) for network download requests.
_HTTP_REQUEST_TIMEOUT = 10
# Chunk size (in bytes) used when streaming a download to report progress.
_HTTP_CHUNK_SIZE = 64 * 1024
# Number of attempts of a file download interrupted by a network error.
_HTTP_DOWNLOAD_ATTEMPTS = 3
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
def _open(url: str, timeout: float, headers: Optional[dict] = None):
    """
    Open "url", translating urllib's network/HTTP errors into RequestError.

    Args:
        url: the url to open.
        timeout: the timeout (in seconds) of the request.
        headers: the extra headers of the request.

    Yields:
        The open response, as returned by urllib.request.urlopen().

    Raises:
        RequestError: if the request fails.
    """
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
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


def _readChunks(response, onBytes: Optional[Callable[[int, int], None]], offset: int = 0) -> Iterator[bytes]:
    """
    Read "response" fully in fixed-size chunks, yielding each chunk.

    Args:
        response: the open response, as returned by urllib.request.urlopen().
        onBytes: if provided, called after each chunk has been consumed with "(bytesRead, totalBytes)",
                 "totalBytes" being -1 if unknown.
        offset: the number of bytes of the content received before "response" (resumed download).

    Yields:
        bytes: the next chunk of the response's body.

    Raises:
        RequestError: if the connection is closed before the whole body announced by "Content-Length" is read.
    """
    contentLength = _contentLength(response)
    total = offset + contentLength if contentLength >= 0 else -1
    bytesRead = offset
    while True:
        chunk = response.read(_HTTP_CHUNK_SIZE)
        if not chunk:
            break
        yield chunk
        # Resumed once the caller has consumed the chunk (e.g. written it to a file).
        bytesRead += len(chunk)
        if onBytes:
            onBytes(bytesRead, total)
    # "read()" returns no data, without error, when the server closes the connection early.
    if total >= 0 and bytesRead < total:
        raise RequestError(f"Incomplete download: received {bytesRead} of {total} bytes.")


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


def fetchWithETag(url: str, timeout: float = _HTTP_REQUEST_TIMEOUT) -> Tuple[bytes, Optional[str]]:
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
        return b"".join(_readChunks(response, onBytes))


def _resumeOffset(response, offset: int) -> int:
    """
    Return the offset at which "response" (to a request for the bytes from "offset") resumes the content:
    "offset" if the server sent the requested range, 0 if it sent the whole content.

    Raises:
        RequestError: if the server sent another range.
    """
    if offset == 0 or response.status != 206:
        return 0
    match = re.match(r"bytes (\d+)-", response.headers.get("Content-Range", ""))
    if not match or int(match.group(1)) != offset:
        raise RequestError(f"Unexpected range in the response: '{response.headers.get('Content-Range')}'.")
    return offset


def fetchToFile(url: str, destination: Path, onBytes: Optional[Callable[[int, int], None]] = None,
                timeout: float = _HTTP_REQUEST_TIMEOUT) -> str:
    """
    GET "url" and stream its content into "destination", reporting progress via "onBytes".
    The content is written to a temporary file next to "destination" first, then moved into place,
    so "destination" is never left partially written.
    A download interrupted by a network error is attempted again, resumed where it stopped when the
    server supports ranges.

    Args:
        url: the url to download.
        destination: the file to write. Its parent folder must exist.
        onBytes: if provided, called after each chunk with "(bytesRead, totalBytes)", "totalBytes"
                 being -1 if unknown. Raising from it aborts the download.
        timeout: the timeout (in seconds) of the request.

    Returns:
        str: the SHA-256 hexdigest of the downloaded content.

    Raises:
        RequestError: if the request fails, or the download is still incomplete after all the attempts.
    """
    destination = Path(destination)
    with atomicOpen(destination, "wb", prefix=f".{destination.name}.") as tmpFile:
        sha256 = hashlib.sha256()
        received = 0
        for attempt in range(1, _HTTP_DOWNLOAD_ATTEMPTS + 1):
            try:
                headers = {"Range": f"bytes={received}-"} if received else None
                with _open(url, timeout, headers) as response:
                    offset = _resumeOffset(response, received)
                    if offset != received:
                        # The server sent the whole content again: start over.
                        tmpFile.seek(0)
                        tmpFile.truncate()
                        sha256 = hashlib.sha256()
                        received = 0
                    for chunk in _readChunks(response, onBytes, offset):
                        tmpFile.write(chunk)
                        sha256.update(chunk)
                        received += len(chunk)
                return sha256.hexdigest()
            except RequestError as exc:
                # Only network errors are worth another attempt, not HTTP errors (e.g. 404).
                if exc.code is not None or attempt == _HTTP_DOWNLOAD_ATTEMPTS:
                    raise
                logging.warning(f"Download of '{url}' interrupted ({exc}), attempt {attempt + 1}/"
                                f"{_HTTP_DOWNLOAD_ATTEMPTS} from byte {received}.")
