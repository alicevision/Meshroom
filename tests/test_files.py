import os
import stat
import sys

import pytest

from meshroom.core.files import atomicOpen, atomicWriteFile


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions")
def test_atomicWriteFileMode(tmp_path):
    # The file gets the permissions of a regular new file, not the owner-only ones of a temporary file.
    path = tmp_path / "file.txt"
    previousUmask = os.umask(0o022)
    try:
        atomicWriteFile(path, "content")
    finally:
        os.umask(previousUmask)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o644


def test_atomicOpenKeepsUmask(tmp_path, monkeypatch):
    # The umask is shared by all the threads: writing a file must not change it, even for an instant.
    def umask(mask):
        raise AssertionError("os.umask() called")
    monkeypatch.setattr(os, "umask", umask)
    atomicWriteFile(tmp_path / "file.txt", "content")
    assert (tmp_path / "file.txt").read_text() == "content"


def test_atomicOpenFailure(tmp_path):
    # The temporary file does not outlive a failure, and the previous content is kept.
    path = tmp_path / "file.bin"
    path.write_bytes(b"previous")
    with pytest.raises(ValueError):
        with atomicOpen(path, "wb") as f:
            f.write(b"new")
            raise ValueError()
    assert path.read_bytes() == b"previous"
    assert list(tmp_path.iterdir()) == [path]
