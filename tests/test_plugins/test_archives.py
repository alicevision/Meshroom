#!/usr/bin/env python
# coding:utf-8

import io
import os
import stat
import tarfile
import zipfile

import pytest

from meshroom.core.plugins.local.archives import extractArchive, isArchive, makeExecutable

# Links cannot always be created on Windows.
requiresLinks = pytest.mark.skipif(os.name == "nt", reason="Creating links requires privileges on Windows.")


def writeZipArchive(path, members):
    """
    Write a zip archive at "path" with "members", as {name: content}. A content can be a tuple
    (content, unixMode) to store Unix permissions, a link being stored with a "stat.S_IFLNK" mode.
    """
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            content, mode = content if isinstance(content, tuple) else (content, None)
            info = zipfile.ZipInfo(name)
            if mode is not None:
                info.create_system = 3
                info.external_attr = mode << 16
            archive.writestr(info, content)
    return path


def writeTarArchive(path, members):
    """
    Write a gzipped tar archive at "path" with "members", as a list of (TarInfo keyword arguments, content).
    """
    with tarfile.open(path, "w:gz") as archive:
        for info, content in members:
            tarInfo = tarfile.TarInfo(info.pop("name"))
            for key, value in info.items():
                setattr(tarInfo, key, value)
            data = content.encode() if content is not None else None
            if data is not None:
                tarInfo.size = len(data)
            archive.addfile(tarInfo, io.BytesIO(data) if data is not None else None)
    return path


def isExecutable(path):
    return bool(path.stat().st_mode & stat.S_IXUSR)


def test_isArchive():
    assert isArchive("tool-linux-x86_64.tar.gz")
    assert isArchive("tool-windows-x86_64.ZIP")
    assert isArchive("tool.tgz")
    assert isArchive("tool.tar.xz")
    assert not isArchive("weights.pt")
    assert not isArchive("tool.gz")


def test_makeExecutable(tmp_path):
    path = tmp_path / "tool"
    path.write_text("tool")
    path.chmod(0o644)
    makeExecutable(path)
    if os.name != "nt":
        assert stat.S_IMODE(path.stat().st_mode) == 0o755


class TestZip:

    def test_singleRootIsUnwrapped(self, tmp_path):
        """ The content of the single root folder of the archive goes directly into the destination. """
        archive = writeZipArchive(tmp_path / "tool.zip", {"root/bin/tool": "tool", "root/data/a.txt": "a"})
        extractArchive(archive, tmp_path / "out")
        assert (tmp_path / "out" / "bin" / "tool").read_text() == "tool"
        assert (tmp_path / "out" / "data" / "a.txt").read_text() == "a"
        # Nothing else is left next to the destination.
        assert sorted(path.name for path in tmp_path.iterdir()) == ["out", "tool.zip"]

    def test_severalRootsAreKept(self, tmp_path):
        archive = writeZipArchive(tmp_path / "tool.zip", {"tool": "tool", "data/a.txt": "a"})
        extractArchive(archive, tmp_path / "out")
        assert (tmp_path / "out" / "tool").read_text() == "tool"
        assert (tmp_path / "out" / "data" / "a.txt").read_text() == "a"

    @pytest.mark.skipif(os.name == "nt", reason="No executable permission on Windows.")
    def test_executablePermissionIsKept(self, tmp_path):
        archive = writeZipArchive(tmp_path / "tool.zip", {"root/tool": ("tool", 0o100755),
                                                          "root/a.txt": ("a", 0o100644)})
        extractArchive(archive, tmp_path / "out")
        assert isExecutable(tmp_path / "out" / "tool")
        assert not isExecutable(tmp_path / "out" / "a.txt")

    @requiresLinks
    def test_links(self, tmp_path):
        """ Links inside the extracted content are created, the others are skipped. """
        archive = writeZipArchive(tmp_path / "tool.zip", {
            "root/lib/libtool.so.1": "lib",
            "root/lib/libtool.so": ("libtool.so.1", stat.S_IFLNK | 0o777),
            "root/up": ("../outside", stat.S_IFLNK | 0o777),
            "root/abs": ("/usr/bin/python", stat.S_IFLNK | 0o777),
        })
        extractArchive(archive, tmp_path / "out")
        assert (tmp_path / "out" / "lib" / "libtool.so").read_text() == "lib"
        assert not (tmp_path / "out" / "up").is_symlink()
        assert not (tmp_path / "out" / "abs").is_symlink()

    @requiresLinks
    def test_linkOutsideOfUnwrappedRoot(self, tmp_path):
        """ A skipped link can leave a single root folder: the links are checked against what is kept. """
        archive = writeZipArchive(tmp_path / "tool.zip", {
            "root/data": "data",
            "root/up": ("..", stat.S_IFLNK | 0o777),
            "root/inside": ("data", stat.S_IFLNK | 0o777),
            "abs": ("/usr/bin/python", stat.S_IFLNK | 0o777),
        })
        extractArchive(archive, tmp_path / "out")
        assert sorted(path.name for path in (tmp_path / "out").iterdir()) == ["data", "inside"]
        assert (tmp_path / "out" / "inside").read_text() == "data"

    def test_unsafePath(self, tmp_path):
        archive = writeZipArchive(tmp_path / "tool.zip", {"root/a.txt": "a", "../evil.txt": "evil"})
        with pytest.raises(ValueError):
            extractArchive(archive, tmp_path / "out")
        assert not (tmp_path / "out").exists()
        assert not (tmp_path.parent / "evil.txt").exists()

    def test_invalidArchive(self, tmp_path):
        archive = tmp_path / "tool.zip"
        archive.write_text("notAZip")
        with pytest.raises(zipfile.BadZipFile):
            extractArchive(archive, tmp_path / "out")
        assert not (tmp_path / "out").exists()


class TestTar:

    @pytest.fixture(autouse=True, params=[True, False], ids=["dataFilter", "noDataFilter"])
    def dataFilter(self, request, monkeypatch):
        """ Run each test with and without the "data" extraction filter of tarfile (missing from older Pythons). """
        if not request.param:
            monkeypatch.delattr(tarfile, "data_filter", raising=False)

    def test_extract(self, tmp_path):
        """ The single root folder is unwrapped and the permissions are kept. """
        archive = writeTarArchive(tmp_path / "tool.tar.gz", [
            ({"name": "root", "type": tarfile.DIRTYPE, "mode": 0o755}, None),
            ({"name": "root/bin/tool", "mode": 0o755}, "tool"),
            ({"name": "root/a.txt", "mode": 0o644}, "a"),
        ])
        extractArchive(archive, tmp_path / "out")
        assert (tmp_path / "out" / "bin" / "tool").read_text() == "tool"
        if os.name != "nt":
            assert isExecutable(tmp_path / "out" / "bin" / "tool")
            assert not isExecutable(tmp_path / "out" / "a.txt")

    @requiresLinks
    def test_links(self, tmp_path):
        """ Links inside the extracted content are created, the others are skipped. """
        archive = writeTarArchive(tmp_path / "tool.tar.gz", [
            ({"name": "root/lib/libtool.so.1"}, "lib"),
            ({"name": "root/lib/libtool.so", "type": tarfile.SYMTYPE, "linkname": "libtool.so.1"}, None),
            ({"name": "root/lib/hard.so", "type": tarfile.LNKTYPE, "linkname": "root/lib/libtool.so.1"}, None),
            ({"name": "root/venv/bin/python", "type": tarfile.SYMTYPE, "linkname": "/github/home/python"}, None),
            ({"name": "root/up", "type": tarfile.SYMTYPE, "linkname": "../outside"}, None),
        ])
        extractArchive(archive, tmp_path / "out")
        assert (tmp_path / "out" / "lib" / "libtool.so").read_text() == "lib"
        assert (tmp_path / "out" / "lib" / "hard.so").read_text() == "lib"
        assert not (tmp_path / "out" / "venv" / "bin" / "python").is_symlink()
        assert not (tmp_path / "out" / "up").is_symlink()

    @requiresLinks
    def test_pathThroughLink(self, tmp_path):
        """ A member cannot be extracted through a link pointing outside of the extracted content. """
        archive = writeTarArchive(tmp_path / "tool.tar.gz", [
            ({"name": "root/dir", "type": tarfile.SYMTYPE, "linkname": "sub"}, None),
            ({"name": "root/sub", "type": tarfile.SYMTYPE, "linkname": ".."}, None),
            ({"name": "root/dir/evil.txt"}, "evil"),
        ])
        # The link "sub" is skipped, so "dir" dangles and the member cannot be extracted.
        with pytest.raises((ValueError, OSError)):
            extractArchive(archive, tmp_path / "out")
        assert not (tmp_path / "out").exists()
        assert not (tmp_path / "evil.txt").exists()

    @requiresLinks
    def test_linkOutsideOfUnwrappedRoot(self, tmp_path):
        """ A skipped link can leave a single root folder: the links are checked against what is kept. """
        archive = writeTarArchive(tmp_path / "tool.tar.gz", [
            ({"name": "root/data"}, "data"),
            ({"name": "root/up", "type": tarfile.SYMTYPE, "linkname": ".."}, None),
            ({"name": "abs", "type": tarfile.SYMTYPE, "linkname": "/usr/bin/python"}, None),
        ])
        extractArchive(archive, tmp_path / "out")
        assert [path.name for path in (tmp_path / "out").iterdir()] == ["data"]

    def test_unsafePath(self, tmp_path):
        archive = writeTarArchive(tmp_path / "tool.tar.gz", [({"name": "../evil.txt"}, "evil")])
        with pytest.raises(ValueError):
            extractArchive(archive, tmp_path / "out")
        assert not (tmp_path / "evil.txt").exists()

    def test_specialFile(self, tmp_path):
        archive = writeTarArchive(tmp_path / "tool.tar.gz", [({"name": "root/fifo", "type": tarfile.FIFOTYPE}, None)])
        with pytest.raises(ValueError):
            extractArchive(archive, tmp_path / "out")
        assert not (tmp_path / "out").exists()
