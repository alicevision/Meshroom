import logging
import os
import stat
import tarfile
import zipfile

from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import List, Optional

from meshroom.core.files import scratchFolder

# Extensions (lowercase) of the archives that are extracted, rather than kept as a single file.
ARCHIVE_EXTENSIONS = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")


def isArchive(fileName: str) -> bool:
    """ Return whether "fileName" is the name of an archive that can be extracted. """
    return fileName.lower().endswith(ARCHIVE_EXTENSIONS)


def makeExecutable(path: Path) -> None:
    """ Make "path" executable by whoever can read it. """
    mode = Path(path).stat().st_mode
    Path(path).chmod(mode | ((mode & 0o444) >> 2))


def extractArchive(archivePath: Path, destination: Path) -> None:
    """
    Extract the zip or tar archive "archivePath" into the new folder "destination".

    An archive holding a single root folder is unwrapped: the content of that folder goes directly into
    "destination". The executable permissions stored in the archive are kept. Links pointing outside
    of the extracted content are skipped with a warning.
    The archive is extracted next to "destination" first, then moved into place, so "destination" is
    never left partially extracted.

    Args:
        archivePath: the archive to extract, with one of ARCHIVE_EXTENSIONS.
        destination: the folder to create. Its parent folder must exist.

    Raises:
        ValueError: if the archive contains an unsafe path, or a member that is not a file, a folder or a link.
        zipfile.BadZipFile, tarfile.TarError: if the archive is invalid.
        OSError: if the archive cannot be read, or extracted.
    """
    destination = Path(destination)
    isZip = Path(archivePath).name.lower().endswith(".zip")
    with scratchFolder(destination.parent, prefix=f".{destination.name}.") as tmpDir:
        # Extract into a sub-folder: the scratch folder itself is created with restricted permissions.
        content = tmpDir / "content"
        content.mkdir()
        if isZip:
            _extractZip(Path(archivePath), content)
        else:
            _extractTar(Path(archivePath), content)

        entries = list(content.iterdir())
        if len(entries) == 1 and entries[0].is_dir() and not entries[0].is_symlink():
            content = entries[0]
        _removeOutsideLinks(content)
        os.rename(content, destination)


def _archiveRoot(names: List[str]) -> Optional[str]:
    """ Return the single root folder of an archive holding the members "names", or None if there is none. """
    partsList = [PurePosixPath(name).parts for name in names]
    partsList = [parts for parts in partsList if parts]
    roots = {parts[0] for parts in partsList}
    if len(roots) == 1 and any(len(parts) > 1 for parts in partsList):
        return roots.pop()
    return None


def _isInside(path: Path, folder: Path) -> bool:
    """ Return whether "path", once its links are resolved, is "folder" or inside it. """
    return Path(os.path.realpath(path)).is_relative_to(os.path.realpath(folder))


def _memberPath(root: Path, name: str) -> Optional[Path]:
    """
    Return the path where the archive member "name" is extracted in "root", or None for the root itself.

    Raises:
        ValueError: if the member would be extracted outside of "root".
    """
    posixPath = PurePosixPath(name)
    if posixPath.is_absolute() or PureWindowsPath(name).drive or ".." in posixPath.parts:
        raise ValueError(f"Unsafe path in archive: '{name}'.")
    if not posixPath.parts:
        return None
    path = root.joinpath(*posixPath.parts)
    # Guard against a member extracted through a link created by a previous member.
    if not _isInside(path.parent, root):
        raise ValueError(f"Unsafe path in archive: '{name}'.")
    return path


def _isLinkInside(folder: Path, target: str, keptRoot: Path) -> bool:
    """
    Return whether a link to "target", relative to "folder", points inside "keptRoot" (the extracted content kept).
    """
    if PurePosixPath(target).is_absolute() or PureWindowsPath(target).drive:
        return False
    return _isInside(folder / target, keptRoot)


def _skipLink(name: str, target: str) -> None:
    logging.warning(f"Skipping link '{name}' -> '{target}' of archive: it points outside of the extracted content.")


def _removeOutsideLinks(root: Path) -> None:
    """
    Remove the links of the folder "root" pointing outside of it. The links of an archive are checked when they
    are extracted, but its single root folder may only be known afterwards, once the skipped links are left out.
    """
    for folder, folderNames, fileNames in os.walk(root):
        for name in folderNames + fileNames:
            path = Path(folder) / name
            if path.is_symlink() and not _isInside(path, root):
                _skipLink(path.relative_to(root).as_posix(), os.readlink(path))
                path.unlink()


def _extractZip(archivePath: Path, root: Path) -> None:
    """ Extract the zip archive "archivePath" into the existing folder "root". See extractArchive(). """
    with zipfile.ZipFile(archivePath) as archive:
        rootName = _archiveRoot(archive.namelist())
        keptRoot = root / rootName if rootName else root
        for info in archive.infolist():
            path = _memberPath(root, info.filename)
            if path is None:
                continue
            # The permissions are only stored by archives created on Unix.
            mode = (info.external_attr >> 16) if info.create_system == 3 else 0
            if stat.S_ISLNK(mode):
                # A link is stored as a file holding its target.
                target = archive.read(info).decode("utf-8")
                if not _isLinkInside(path.parent, target, keptRoot):
                    _skipLink(info.filename, target)
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    os.symlink(target, path)
                except OSError as exc:
                    # e.g. on Windows, without the privilege to create links.
                    logging.warning(f"Failed to create link '{info.filename}' -> '{target}' of archive: {exc}")
                continue
            extractedPath = archive.extract(info, root)
            if not info.is_dir() and mode & 0o111:
                makeExecutable(Path(extractedPath))


def _extractTar(archivePath: Path, root: Path) -> None:
    """ Extract the tar archive "archivePath" into the existing folder "root". See extractArchive(). """
    # The "data" filter (Python >= 3.12, backported to 3.9.17, 3.10.12 and 3.11.4) also refuses special
    # files, and clears the high and group/other write permission bits. Without it, this is done here.
    hasDataFilter = hasattr(tarfile, "data_filter")
    with tarfile.open(archivePath, "r:*") as archive:
        members = archive.getmembers()
        rootName = _archiveRoot([member.name for member in members])
        keptRoot = root / rootName if rootName else root
        for member in members:
            path = _memberPath(root, member.name)
            if path is None:
                continue
            if member.issym() or member.islnk():
                # A hard link target is relative to the archive root, a symbolic link target to the link's folder.
                linkFolder = root if member.islnk() else path.parent
                if not _isLinkInside(linkFolder, member.linkname, keptRoot):
                    _skipLink(member.name, member.linkname)
                    continue
            elif not (member.isfile() or member.isdir()):
                raise ValueError(f"Unsupported member in archive: '{member.name}'.")
            if hasDataFilter:
                archive.extract(member, root, filter="data")
            else:
                member.mode &= 0o755
                archive.extract(member, root)
