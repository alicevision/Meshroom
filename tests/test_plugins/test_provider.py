#!/usr/bin/env python
# coding:utf-8

from meshroom.core.plugins.record import PluginRecord
from meshroom.core.plugins.provider import ArchivePluginProvider, GithubPluginProvider, getPluginProviderFromUrl

GITHUB_URL = "https://github.com/myPublisher/myRepo"
ARCHIVE_URL = "https://example.com/plugin.zip"


class TestGetPluginProviderFromUrl:

    def test_github(self):
        """ A GitHub repository url gives a GithubPluginProvider bound to its publisher and repository. """
        provider = getPluginProviderFromUrl(GITHUB_URL)
        assert isinstance(provider, GithubPluginProvider)
        assert provider.publisher == "myPublisher"
        assert provider.repo == "myRepo"

    def test_archive(self):
        """ A zip url gives an ArchivePluginProvider. """
        assert isinstance(getPluginProviderFromUrl(ARCHIVE_URL), ArchivePluginProvider)

    def test_unsupported(self):
        """ An url that no provider recognizes gives None. """
        assert getPluginProviderFromUrl("https://example.com/plugin") is None
        assert getPluginProviderFromUrl("https://github.com/myPublisher/myRepo/tree/main") is None


class TestGithubPluginProvider:

    def test_archiveUrl(self):
        """ The archive url points to the zip of the requested ref, the commit for "<branch>+<commit>". """
        provider = GithubPluginProvider("myPublisher", "myRepo")
        assert provider.archiveUrl("v1.0") == f"{GITHUB_URL}/archive/v1.0.zip"
        assert provider.archiveUrl("main+abc123") == f"{GITHUB_URL}/archive/abc123.zip"

    def test_completeRecordFromUrl(self):
        """ A record without name and publisher takes them from the repository. """
        record = GithubPluginProvider("myPublisher", "myRepo").completeRecord(PluginRecord("", "1.0", "", GITHUB_URL))
        assert record.name == "myRepo"
        assert record.publisher == "myPublisher"
        assert record.version == "1.0"

    def test_completeRecordKeepsValues(self):
        """ A record with a name and a publisher is kept as is. """
        record = PluginRecord("myPlugin", "1.0", "me", GITHUB_URL)
        assert GithubPluginProvider("myPublisher", "myRepo").completeRecord(record) is record

    def test_completeRecordWithoutVersion(self):
        """ A record without version is rejected. """
        record = PluginRecord("myPlugin", "", "me", GITHUB_URL)
        assert GithubPluginProvider("myPublisher", "myRepo").completeRecord(record) is None


class TestArchivePluginProvider:

    def test_archiveUrl(self):
        """ The archive url is the provider url, whatever the version. """
        assert ArchivePluginProvider(ARCHIVE_URL).archiveUrl("1.0") == ARCHIVE_URL

    def test_completeRecord(self):
        """ A record with a name is kept as is, a record without one is rejected. """
        provider = ArchivePluginProvider(ARCHIVE_URL)
        record = PluginRecord("myPlugin", "", "", ARCHIVE_URL)
        assert provider.completeRecord(record) is record
        assert provider.completeRecord(PluginRecord("", "1.0", "me", ARCHIVE_URL)) is None
