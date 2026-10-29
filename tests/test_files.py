import os
import stat
import sys

import pytest

from meshroom.core.files import atomicWriteFile, defaultFileMode


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions")
def test_atomicWriteFileMode(tmp_path):
    # The file gets the permissions of a regular new file, not the owner-only ones of a temporary file.
    path = tmp_path / "file.txt"
    previousUmask = os.umask(0o022)
    try:
        assert defaultFileMode() == 0o644
        atomicWriteFile(path, "content")
    finally:
        os.umask(previousUmask)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o644
