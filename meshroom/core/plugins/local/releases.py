import json
import platform
import re

from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote

from meshroom.core.httpUtils import RequestError, fetchWithProgress

# The base url of the GitHub REST API.
_GITHUB_API_URL = "https://api.github.com"

# The words identifying an operating system in the name of a release file.
_SYSTEM_KEYWORDS = {
    "linux": ("linux",),
    "windows": ("windows", "win64", "win32", "win"),
    "macos": ("macos", "darwin", "osx", "mac"),
}
# The words identifying a processor architecture in the name of a release file.
_ARCH_KEYWORDS = {
    "x86_64": ("x86_64", "x86-64", "amd64", "x64"),
    "arm64": ("arm64", "aarch64"),
}
# The extensions (lowercase) of release files that describe another file (checksums, signatures).
_IGNORED_EXTENSIONS = (".sha256", ".sha256sum", ".sha512", ".md5", ".sig", ".asc")


class ReleaseError(Exception):
    """ Raised when the file of a release cannot be found. """


class ReleaseFile:
    """
    A file attached to a GitHub release.

    Members:
        name: the file name.
        url: the url to download the file from.
        sha256: the SHA-256 hexdigest of the file published by GitHub (lowercase), or None if not published.
    """
    def __init__(self, name: str, url: str, sha256: Optional[str] = None):
        self.name = name
        self.url = url
        self.sha256 = sha256

    def __repr__(self) -> str:
        return f"ReleaseFile({self.name!r}, {self.url!r}, {self.sha256!r})"


def currentPlatform() -> Tuple[Optional[str], Optional[str]]:
    """
    Return the operating system ("linux", "windows", "macos") and the processor architecture
    ("x86_64", "arm64") of this machine, each being None if it is not one of these.
    """
    system = {"Linux": "linux", "Windows": "windows", "Darwin": "macos"}.get(platform.system())
    machine = platform.machine().lower()
    arch = next((arch for arch, keywords in _ARCH_KEYWORDS.items() if machine in keywords), None)
    return system, arch


def fetchReleaseFiles(release: str) -> List[ReleaseFile]:
    """
    Return the files attached to the GitHub release "release", using the GitHub API without authentication.

    Args:
        release: the release, as "<owner>/<repository>@<tag>".

    Returns:
        list[ReleaseFile]: the files of the release.

    Raises:
        ReleaseError: if the release cannot be found or read.
    """
    repository, _, tag = release.rpartition("@")
    url = f"{_GITHUB_API_URL}/repos/{repository}/releases/tags/{quote(tag, safe='')}"
    try:
        content = fetchWithProgress(url)
    except RequestError as exc:
        if exc.code == 404:
            raise ReleaseError(f"Release '{tag}' not found in GitHub repository '{repository}'.") from exc
        if exc.code in (403, 429):
            raise ReleaseError("GitHub API rate limit exceeded (60 requests per hour without authentication), "
                               "try again later.") from exc
        raise ReleaseError(f"Failed to get release '{release}' from '{url}': {exc}") from exc

    try:
        return [ReleaseFile(entry["name"], entry["browser_download_url"], _parseDigest(entry.get("digest")))
                for entry in json.loads(content)["assets"]]
    except (ValueError, KeyError, TypeError) as exc:
        raise ReleaseError(f"Invalid description of release '{release}' from '{url}'.") from exc


def _parseDigest(digest) -> Optional[str]:
    """ Return the SHA-256 hexdigest of a GitHub "digest" ("sha256:<hexdigest>"), or None if there is none. """
    match = re.match(r"^sha256:([0-9a-fA-F]{64})$", digest) if isinstance(digest, str) else None
    return match.group(1).lower() if match else None


def _keywordsIn(name: str, keywords: Dict[str, Tuple[str, ...]]) -> Set[str]:
    """ Return the keys of "keywords" whose words appear in "name", as whole words. """
    name = name.lower()
    return {key for key, words in keywords.items()
            if any(re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", name) for word in words)}


def selectReleaseFile(files: List[ReleaseFile], system: Optional[str], arch: Optional[str]) -> ReleaseFile:
    """
    Return the file of a release to install on the operating system "system" with the architecture "arch".

    The operating system and the architecture of a file are read from its name (e.g.
    "tool-1.0-linux-x86_64.tar.gz"). A file naming no architecture fits any, if no file names the one of
    this machine. A release whose files name no operating system is used as is if it has a single file.

    Args:
        files: the files of the release.
        system: the operating system, as returned by currentPlatform().
        arch: the processor architecture, as returned by currentPlatform().

    Returns:
        ReleaseFile: the single file matching the platform.

    Raises:
        ReleaseError: if no file, or several files, match the platform.
    """
    candidates = [file for file in files if not file.name.lower().endswith(_IGNORED_EXTENSIONS)]
    systems = {file.name: _keywordsIn(file.name, _SYSTEM_KEYWORDS) for file in candidates}

    if not any(systems.values()):
        matches = candidates
    else:
        matches = [file for file in candidates if systems[file.name] == {system}]
        archs = {file.name: _keywordsIn(file.name, _ARCH_KEYWORDS) for file in matches}
        matches = ([file for file in matches if archs[file.name] == {arch}]
                   or [file for file in matches if not archs[file.name]])

    if len(matches) == 1:
        return matches[0]
    platformName = f"{system or platform.system()} {arch or platform.machine()}"
    if not matches:
        names = ", ".join(f"'{file.name}'" for file in files) or "none"
        raise ReleaseError(f"No file of the release matches this platform ({platformName}). Release files: {names}.")
    names = ", ".join(f"'{file.name}'" for file in matches)
    raise ReleaseError(f"Several files of the release match this platform ({platformName}): {names}.")
