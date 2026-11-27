#!/usr/bin/env python
# coding:utf-8

from meshroom.core.plugins.local.releases import ReleaseFile, selectReleaseFile


def test_selectReleaseFile():
    """ The file of a release is chosen from the operating system and the architecture named in its name. """
    names = ["tool-1.0-linux-x86_64.tar.gz", "tool-1.0-linux-aarch64.tar.gz", "tool-1.0-win64.zip",
             "tool-1.0-macos.zip", "tool-1.0-linux-x86_64.tar.gz.sha256"]
    files = [ReleaseFile(name, f"https://example.org/{name}") for name in names]
    assert selectReleaseFile(files, "linux", "x86_64").name == "tool-1.0-linux-x86_64.tar.gz"
    assert selectReleaseFile(files, "linux", "arm64").name == "tool-1.0-linux-aarch64.tar.gz"
    assert selectReleaseFile(files, "windows", "x86_64").name == "tool-1.0-win64.zip"
    # A file naming no architecture fits any.
    assert selectReleaseFile(files, "macos", "arm64").name == "tool-1.0-macos.zip"
