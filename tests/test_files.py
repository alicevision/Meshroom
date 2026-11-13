#!/usr/bin/env python
# coding:utf-8

import os

import pytest

from meshroom.core.files import atomicWriteFile
from .utils import writeFile


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions")
def test_atomicWriteFilePermissions(tmp_path):
    """ A file written atomically gets the permissions of a new regular file, not the owner-only ones of a temporary file. """
    reference = writeFile(tmp_path / "reference.txt")
    atomicWriteFile(tmp_path / "written.txt", "content")
    assert (tmp_path / "written.txt").stat().st_mode == reference.stat().st_mode
