#!/usr/bin/env python
# coding:utf-8

import json
import time

from meshroom.core.plugins.registry import PluginRegistry
from ..utils import writeFile

FILE_URL = "https://example.com/registry.json"


class TestUpdateRecords:

    def test_emptyBeforeUpdate(self, tmp_path):
        """ A registry holds no records until they are updated. """
        content = {"entries": [{"url": "https://github.com/pub/repo", "versions": ["1.0"]}]}
        path = writeFile(tmp_path / "registry.json", json.dumps(content))
        assert PluginRegistry(path).records == []

    def test_missingFile(self, tmp_path):
        """ A missing registry file fails the update instead of raising. """
        registry = PluginRegistry(tmp_path / "registry.json")
        assert not registry.updateRecords()
        assert registry.records == []

    def test_malformedJson(self, tmp_path):
        """ Malformed JSON content fails the update instead of raising. """
        path = writeFile(tmp_path / "registry.json", "{not valid json")
        registry = PluginRegistry(path)
        assert not registry.updateRecords()
        assert registry.records == []

    def test_invalidTopLevelType(self, tmp_path):
        """ A JSON document that is not an object is rejected. """
        path = writeFile(tmp_path / "registry.json", json.dumps(["not", "an", "object"]))
        registry = PluginRegistry(path)
        assert not registry.updateRecords()
        assert registry.records == []

    def test_missingEntries(self, tmp_path):
        """ A registry without "entries" is rejected. """
        path = writeFile(tmp_path / "registry.json", json.dumps({"fileUrl": FILE_URL}))
        registry = PluginRegistry(path)
        assert not registry.updateRecords()
        assert registry.records == []

    def test_noEntries(self, tmp_path):
        """ A registry with an empty list of entries has no records. """
        path = writeFile(tmp_path / "registry.json", json.dumps({"entries": []}))
        registry = PluginRegistry(path)
        assert registry.updateRecords()
        assert registry.records == []

    def test_fullGithubEntry(self, tmp_path):
        """ A complete entry populates every field, and is stored by name. """
        content = {"entries": [{
            "name": "myPlugin",
            "url": "https://github.com/myPublisher/myRepo",
            "versions": ["1.2", "1.1"],
            "publisher": "myPublisher",
            "description": "A plugin that does things.",
            "authors": ["Alice", "Bob"],
            "requirements": "CUDA >= X.X",
        }]}
        path = writeFile(tmp_path / "registry.json", json.dumps(content))

        registry = PluginRegistry(path)
        assert registry.updateRecords()

        assert [record.name for record in registry.records] == ["myPlugin"]
        record = registry.records[0]
        assert record.name == "myPlugin"
        assert record.url == "https://github.com/myPublisher/myRepo"
        assert record.version == "1.2"
        assert record.versions == ["1.2", "1.1"]
        assert record.publisher == "myPublisher"
        assert record.description == "A plugin that does things."
        assert record.authors == ["Alice", "Bob"]
        assert record.requirements == "CUDA >= X.X"

    def test_githubNameAndPublisherFromUrl(self, tmp_path):
        """ A GitHub entry without name and publisher takes them from its url. """
        content = {"entries": [{"url": "https://github.com/myPublisher/myRepo", "versions": ["1.0"]}]}
        path = writeFile(tmp_path / "registry.json", json.dumps(content))

        registry = PluginRegistry(path)
        assert registry.updateRecords()

        assert [record.name for record in registry.records] == ["myRepo"]
        assert registry.records[0].name == "myRepo"
        assert registry.records[0].publisher == "myPublisher"

    def test_archiveEntryWithoutName(self, tmp_path):
        """ An archive entry without a name is rejected. """
        content = {"entries": [{"url": "https://example.com/plugin.zip", "versions": ["1.0"]}]}
        path = writeFile(tmp_path / "registry.json", json.dumps(content))
        registry = PluginRegistry(path)
        assert not registry.updateRecords()
        assert registry.records == []

    def test_invalidNameFromUrl(self, tmp_path):
        """ An entry named after a repository whose name is not a valid plugin name is rejected. """
        content = {"entries": [{"url": "https://github.com/myPublisher/..", "versions": ["1.0"]}]}
        path = writeFile(tmp_path / "registry.json", json.dumps(content))
        registry = PluginRegistry(path)
        assert not registry.updateRecords()
        assert registry.records == []

    def test_oneInvalidEntryInvalidatesRegistry(self, tmp_path):
        """ A single invalid entry invalidates the whole registry, even if the other ones are valid. """
        content = {"entries": [
            {"url": "https://github.com/pub/good", "versions": ["1.0"]},
            {"url": "not a known plugin source"},
        ]}
        path = writeFile(tmp_path / "registry.json", json.dumps(content))
        registry = PluginRegistry(path)
        assert not registry.updateRecords()
        assert registry.records == []

    def test_duplicateNameKeepsFirst(self, tmp_path):
        """ When several entries share a name, the first one is kept. """
        content = {"entries": [
            {"name": "dup", "url": "https://example.com/first.zip", "versions": ["1.0"]},
            {"name": "dup", "url": "https://example.com/second.zip", "versions": ["2.0"]},
        ]}
        path = writeFile(tmp_path / "registry.json", json.dumps(content))

        registry = PluginRegistry(path)
        assert registry.updateRecords()

        assert [record.name for record in registry.records] == ["dup"]
        assert registry.records[0].url == "https://example.com/first.zip"

    def test_updateReplacesRecords(self, tmp_path):
        """ A successful update replaces the previously stored records. """
        path = writeFile(tmp_path / "registry.json", json.dumps(
            {"entries": [{"url": "https://github.com/pub/first", "versions": ["1.0"]}]}))
        registry = PluginRegistry(path)
        assert registry.updateRecords()
        assert [record.name for record in registry.records] == ["first"]

        writeFile(path, json.dumps({"entries": [{"url": "https://github.com/pub/second", "versions": ["1.0"]}]}))
        assert registry.updateRecords()
        assert [record.name for record in registry.records] == ["second"]

    def test_failedUpdateClearsRecords(self, tmp_path):
        """ A failed update leaves the registry without any record. """
        path = writeFile(tmp_path / "registry.json", json.dumps(
            {"entries": [{"url": "https://github.com/pub/first", "versions": ["1.0"]}]}))
        registry = PluginRegistry(path)
        assert registry.updateRecords()
        assert [record.name for record in registry.records] == ["first"]

        writeFile(path, "{not valid json")
        assert not registry.updateRecords()
        assert registry.records == []


class TestProperties:

    def test_name(self, tmp_path):
        """ The registry is named after its file. """
        assert PluginRegistry(tmp_path / "myRegistry.json").name == "myRegistry"

    def test_records(self, tmp_path):
        """ The records property lists the stored records, and notifies when they are updated. """
        content = {"entries": [{"url": "https://github.com/pub/repo", "versions": ["1.0"]}]}
        path = writeFile(tmp_path / "registry.json", json.dumps(content))
        registry = PluginRegistry(path)
        notifications = []
        registry.recordsChanged.connect(lambda: notifications.append(True))

        assert registry.records == []

        assert registry.updateRecords()
        assert [record.name for record in registry.records] == ["repo"]
        assert len(notifications) == 1

        writeFile(path, "{not valid json")
        assert not registry.updateRecords()
        assert registry.records == []
        assert len(notifications) == 2

    def test_getRecord(self, tmp_path):
        """ getRecord looks up a stored record by name, and returns None if it is not found. """
        content = {"entries": [{"url": "https://github.com/pub/repo", "versions": ["1.0"]}]}
        path = writeFile(tmp_path / "registry.json", json.dumps(content))
        registry = PluginRegistry(path)
        registry.updateRecords()

        record = registry.getRecord("repo")
        assert record is not None
        assert record.name == "repo"

        assert registry.getRecord("unknown") is None


class TestMatchesRemote:

    def test_missingFile(self, tmp_path):
        """ A missing registry file does not match its remote. """
        assert not PluginRegistry(tmp_path / "registry.json").matchesRemote()

    def test_missingFileUrl(self, tmp_path):
        """ A registry without "fileUrl" cannot be compared to a remote. """
        path = writeFile(tmp_path / "registry.json", json.dumps({"entries": []}))
        writeFile(tmp_path / "registry.json.etag", f"{time.time()}\nW/\"1\"")
        assert not PluginRegistry(path).matchesRemote()

    def test_missingEtagFile(self, tmp_path):
        """ A registry that was never fetched does not match its remote. """
        path = writeFile(tmp_path / "registry.json", json.dumps({"fileUrl": FILE_URL, "entries": []}))
        assert not PluginRegistry(path).matchesRemote()

    def test_withinTTL(self, tmp_path):
        """ A registry fetched less than a TTL ago matches its remote without checking it. """
        path = writeFile(tmp_path / "registry.json", json.dumps({"fileUrl": FILE_URL, "entries": []}))
        writeFile(tmp_path / "registry.json.etag", f"{time.time()}\n")
        assert PluginRegistry(path).matchesRemote()

    def test_expiredWithoutEtag(self, tmp_path):
        """ Once the TTL has expired, a registry without ETag does not match its remote. """
        path = writeFile(tmp_path / "registry.json", json.dumps({"fileUrl": FILE_URL, "entries": []}))
        writeFile(tmp_path / "registry.json.etag", "0\n")
        assert not PluginRegistry(path).matchesRemote()

    def test_malformedTimestamp(self, tmp_path):
        """ A malformed ".etag" file does not match its remote. """
        path = writeFile(tmp_path / "registry.json", json.dumps({"fileUrl": FILE_URL, "entries": []}))
        writeFile(tmp_path / "registry.json.etag", "yesterday\nW/\"1\"")
        assert not PluginRegistry(path).matchesRemote()


class TestFetch:
    """ The remote registry files are local files, fetched with "file://" urls. """

    def test_fetchUrl(self, tmp_path):
        """ A fetched registry is written locally, and its records can be loaded. """
        remote = writeFile(tmp_path / "remote" / "registry.json", json.dumps(
            {"entries": [{"url": "https://github.com/pub/repo", "versions": ["1.0"]}]}))
        registry = PluginRegistry(tmp_path / "registry.json")

        assert registry.fetch(remote.as_uri()) == tmp_path / "registry.json"
        assert (tmp_path / "registry.json").read_text() == remote.read_text()
        assert registry.updateRecords()
        assert [record.name for record in registry.records] == ["repo"]

    def test_fetchedMatchesRemote(self, tmp_path):
        """ A fetched registry matches its remote until the TTL expires, then needs an ETag to be checked. """
        remote = tmp_path / "remote" / "registry.json"
        writeFile(remote, json.dumps({"fileUrl": remote.as_uri(), "entries": []}))
        registry = PluginRegistry(tmp_path / "registry.json")
        registry.fetch(remote.as_uri())

        assert registry.matchesRemote()
        # "file://" urls have no ETag.
        assert not registry.matchesRemote(useTTL=False)

    def test_refreshFromFileUrl(self, tmp_path):
        """ Without url, the registry is fetched again from the "fileUrl" of its local file. """
        remote = tmp_path / "remote" / "registry.json"
        writeFile(remote, json.dumps({"fileUrl": remote.as_uri(),
                                      "entries": [{"url": "https://github.com/pub/second", "versions": ["1.0"]}]}))
        path = writeFile(tmp_path / "registry.json", json.dumps({"fileUrl": remote.as_uri(), "entries": []}))
        registry = PluginRegistry(path)

        assert registry.fetch() == path
        assert registry.updateRecords()
        assert [record.name for record in registry.records] == ["second"]

    def test_missingFileUrl(self, tmp_path):
        """ Without url, a registry without "fileUrl" cannot be fetched. """
        path = writeFile(tmp_path / "registry.json", json.dumps({"entries": []}))
        assert PluginRegistry(path).fetch() is None

    def test_missingRemote(self, tmp_path):
        """ A registry whose remote does not exist is not written. """
        registry = PluginRegistry(tmp_path / "registry.json")
        assert registry.fetch((tmp_path / "missing.json").as_uri()) is None
        assert not (tmp_path / "registry.json").exists()

    def test_invalidRemote(self, tmp_path):
        """ An invalid remote (malformed JSON, or not a JSON object) leaves the local registry untouched. """
        path = writeFile(tmp_path / "registry.json", json.dumps({"entries": []}))
        registry = PluginRegistry(path)
        for content in ("{not valid json", json.dumps(["not", "an", "object"])):
            remote = writeFile(tmp_path / "remote" / "registry.json", content)
            assert registry.fetch(remote.as_uri()) is None
            assert json.loads(path.read_text()) == {"entries": []}
