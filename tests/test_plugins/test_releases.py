#!/usr/bin/env python
# coding:utf-8

import json

import pytest

from meshroom.core.plugins.local import releases
from meshroom.core.plugins.local.releases import ReleaseError, ReleaseFile, fetchReleaseFiles, selectReleaseFile
from ..utils import writeFile


def releaseFiles(*names):
    return [ReleaseFile(name, f"https://example.com/{name}") for name in names]


def selectedName(names, system, arch):
    return selectReleaseFile(releaseFiles(*names), system, arch).name


class TestSelectReleaseFile:

    # The files of the RNb-NeuS2 v2.0.2 release.
    RNBNEUS2 = ("RNb-NeuS2-2.0.2-linux-x86_64-cu124-py311.tar.gz", "RNb-NeuS2-2.0.2-windows-x86_64-cu124-py311.zip")

    def test_system(self):
        assert selectedName(self.RNBNEUS2, "linux", "x86_64") == self.RNBNEUS2[0]
        assert selectedName(self.RNBNEUS2, "windows", "x86_64") == self.RNBNEUS2[1]

    def test_noMatch(self):
        """ The error lists the files of the release. """
        with pytest.raises(ReleaseError, match="RNb-NeuS2-2.0.2-linux"):
            selectReleaseFile(releaseFiles(*self.RNBNEUS2), "macos", "arm64")
        with pytest.raises(ReleaseError):
            selectReleaseFile(releaseFiles(*self.RNBNEUS2), "linux", "arm64")
        with pytest.raises(ReleaseError):
            selectReleaseFile(releaseFiles(*self.RNBNEUS2), None, None)

    def test_arch(self):
        names = ("tool-linux-x86_64.tar.gz", "tool-linux-aarch64.tar.gz", "tool-macOS-arm64.zip", "tool-win64.zip")
        assert selectedName(names, "linux", "x86_64") == "tool-linux-x86_64.tar.gz"
        assert selectedName(names, "linux", "arm64") == "tool-linux-aarch64.tar.gz"
        assert selectedName(names, "macos", "arm64") == "tool-macOS-arm64.zip"
        assert selectedName(names, "windows", "x86_64") == "tool-win64.zip"

    def test_windowsArch(self):
        names = ("tool-win32.zip", "tool-win64.zip")
        assert selectedName(names, "windows", "x86_64") == "tool-win64.zip"
        # A file for 32-bit Windows runs on any architecture, unlike a file for x86_64.
        assert selectedName(names, "windows", "arm64") == "tool-win32.zip"
        assert selectedName(("tool-win32.zip",), "windows", "x86_64") == "tool-win32.zip"
        with pytest.raises(ReleaseError, match="No file"):
            selectReleaseFile(releaseFiles("tool-win64.zip"), "windows", "arm64")
        # The architecture named by the file prevails.
        assert selectedName(("tool-win64-x64.zip", "tool-win64-arm64.zip"), "windows", "arm64") == "tool-win64-arm64.zip"
        assert selectedName(("tool-win32-x64.zip", "tool-win32-arm64.zip"), "windows", "x86_64") == "tool-win32-x64.zip"

    def test_archSynonyms(self):
        names = ("tool-windows-amd64.zip", "tool-darwin-x64.tar.gz", "tool-osx-arm64.tar.gz")
        assert selectedName(names, "windows", "x86_64") == "tool-windows-amd64.zip"
        assert selectedName(names, "macos", "x86_64") == "tool-darwin-x64.tar.gz"
        assert selectedName(names, "macos", "arm64") == "tool-osx-arm64.tar.gz"

    def test_anyArch(self):
        """ A file naming no architecture is used when no file names the one of this machine. """
        names = ("tool-linux.tar.gz", "tool-linux-arm64.tar.gz", "tool-windows.zip")
        assert selectedName(names, "linux", "x86_64") == "tool-linux.tar.gz"
        assert selectedName(names, "linux", "arm64") == "tool-linux-arm64.tar.gz"
        assert selectedName(names, "windows", "arm64") == "tool-windows.zip"

    def test_wholeWords(self):
        """ System words only match as whole words. """
        names = ("darwinism-linux.tar.gz", "machine-windows.zip")
        assert selectedName(names, "linux", "x86_64") == "darwinism-linux.tar.gz"
        assert selectedName(names, "windows", "x86_64") == "machine-windows.zip"

    def test_checksumsAreIgnored(self):
        names = self.RNBNEUS2 + tuple(f"{name}.sha256" for name in self.RNBNEUS2)
        assert selectedName(names, "linux", "x86_64") == self.RNBNEUS2[0]

    def test_ambiguous(self):
        names = ("tool-linux-x86_64-cu118.tar.gz", "tool-linux-x86_64-cu124.tar.gz")
        with pytest.raises(ReleaseError, match="Several files"):
            selectReleaseFile(releaseFiles(*names), "linux", "x86_64")

    def test_platformIndependentFile(self):
        """ A release whose single file names no operating system fits every platform. """
        assert selectedName(("model.pth",), "windows", "x86_64") == "model.pth"
        assert selectedName(("model.pth", "model.pth.sha256"), None, None) == "model.pth"
        with pytest.raises(ReleaseError):
            selectReleaseFile(releaseFiles("a.pth", "b.pth"), "linux", "x86_64")


class TestFetchReleaseFiles:

    @pytest.fixture(autouse=True)
    def api(self, tmp_path, monkeypatch):
        """ Serve the GitHub API from files in "tmp_path/api". """
        monkeypatch.setattr(releases, "_GITHUB_API_URL", (tmp_path / "api").as_uri())
        return tmp_path / "api"

    def test_fetch(self, api):
        writeFile(api / "repos" / "myOrg" / "myRepo" / "releases" / "tags" / "v1.0.0", json.dumps({"assets": [
            {"name": "tool-linux.tar.gz", "browser_download_url": "https://example.com/tool-linux.tar.gz",
             "digest": "sha256:" + "A" * 64},
            {"name": "tool-windows.zip", "browser_download_url": "https://example.com/tool-windows.zip",
             "digest": None},
        ]}))

        files = fetchReleaseFiles("myOrg/myRepo@v1.0.0")

        assert [(file.name, file.url, file.sha256) for file in files] == [
            ("tool-linux.tar.gz", "https://example.com/tool-linux.tar.gz", "a" * 64),
            ("tool-windows.zip", "https://example.com/tool-windows.zip", None),
        ]

    def test_missingRelease(self):
        with pytest.raises(ReleaseError):
            fetchReleaseFiles("myOrg/myRepo@v1.0.0")

    def test_invalidResponse(self, api):
        writeFile(api / "repos" / "myOrg" / "myRepo" / "releases" / "tags" / "v1.0.0", json.dumps({"message": "?"}))
        with pytest.raises(ReleaseError, match="Invalid"):
            fetchReleaseFiles("myOrg/myRepo@v1.0.0")


def test_currentPlatform(monkeypatch):
    monkeypatch.setattr(releases.platform, "system", lambda: "Windows")
    monkeypatch.setattr(releases.platform, "machine", lambda: "AMD64")
    assert releases.currentPlatform() == ("windows", "x86_64")
    monkeypatch.setattr(releases.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(releases.platform, "machine", lambda: "arm64")
    assert releases.currentPlatform() == ("macos", "arm64")
    monkeypatch.setattr(releases.platform, "system", lambda: "Linux")
    monkeypatch.setattr(releases.platform, "machine", lambda: "riscv64")
    assert releases.currentPlatform() == ("linux", None)
