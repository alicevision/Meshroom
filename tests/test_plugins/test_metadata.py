#!/usr/bin/env python
# coding:utf-8

import json

from meshroom.core.plugins.metadata import PluginAsset, PluginMetadata
from ..utils import writeFile


class TestLoadJsonMetadata:

    def test_missingFile(self, tmp_path):
        """ A missing metadata file yields None instead of raising. """
        assert PluginMetadata.loadJson(tmp_path / "plugin.lock") is None

    def test_malformedJson(self, tmp_path):
        """ Malformed JSON content yields None instead of raising. """
        path = writeFile(tmp_path / "plugin.lock", "{not valid json")
        assert PluginMetadata.loadJson(path) is None

    def test_invalidTopLevelType(self, tmp_path):
        """ A JSON document that is neither a list nor an object is rejected. """
        path = writeFile(tmp_path / "plugin.lock", json.dumps("not a list or an object"))
        assert PluginMetadata.loadJson(path) is None

    def test_legacyListFormat(self, tmp_path):
        """ The legacy "config.json" format (a bare list) is only read as "env" entries. """
        content = [{"key": "MY_VAR", "type": "string", "value": "myValue"}]
        path = writeFile(tmp_path / "config.json", json.dumps(content))

        metadata = PluginMetadata.loadJson(path)

        assert metadata is not None
        assert metadata.name is None
        assert metadata.version is None
        assert metadata.publisher is None
        assert metadata.authors == []
        assert metadata.description is None
        assert metadata.requirements is None
        assert metadata.license is None
        assert metadata.env == content

    def test_fullDictFormat(self, tmp_path):
        """ A complete "plugin.lock"-style object populates every field. """
        content = {
            "name": "my-plugin",
            "version": "1.2.3",
            "publisher": "my-publisher",
            "authors": ["Alice", "Bob"],
            "description": "A plugin that does things.",
            "requirements": "CUDA >= X.X",
            "license": "MIT",
            "env": [{"key": "MY_VAR", "type": "string", "value": "myValue"}],
        }
        path = writeFile(tmp_path / "plugin.lock", json.dumps(content))

        metadata = PluginMetadata.loadJson(path)

        assert metadata is not None
        assert metadata.name == "my-plugin"
        assert metadata.version == "1.2.3"
        assert metadata.publisher == "my-publisher"
        assert metadata.authors == ["Alice", "Bob"]
        assert metadata.description == "A plugin that does things."
        assert metadata.requirements == "CUDA >= X.X"
        assert metadata.license == "MIT"
        assert metadata.env == content["env"]

    def test_invalidNameVersionPublisherAreIgnored(self, tmp_path):
        """ Invalid "name"/"version"/"publisher" values are dropped, not propagated. """
        content = {
            "name": "@invalid_name",
            "version": "not a version",
            "publisher": "invalid publisher",
        }
        path = writeFile(tmp_path / "plugin.lock", json.dumps(content))

        metadata = PluginMetadata.loadJson(path)

        assert metadata is not None
        assert metadata.name is None
        assert metadata.version is None
        assert metadata.publisher is None

    def test_authorsMustBeStrings(self, tmp_path):
        """ Non-string entries in "authors" are dropped, valid ones are kept. """
        content = {"authors": ["Alice", 42, {"name": "Bob"}, "Carol"]}
        path = writeFile(tmp_path / "plugin.lock", json.dumps(content))

        metadata = PluginMetadata.loadJson(path)

        assert metadata is not None
        assert metadata.authors == ["Alice", "Carol"]

    def test_descriptionRequirementsAndLicenseMustBeStrings(self, tmp_path):
        """ Non-string "description"/"requirements"/"license" values are dropped, not propagated. """
        content = {"description": 42, "requirements": ["not", "a", "string"], "license": {"text": "MIT"}}
        path = writeFile(tmp_path / "plugin.lock", json.dumps(content))

        metadata = PluginMetadata.loadJson(path)

        assert metadata is not None
        assert metadata.description is None
        assert metadata.requirements is None
        assert metadata.license is None

    def test_nonListEnvIsIgnored(self, tmp_path):
        """ A non-list "env" value is ignored, falling back to an empty list. """
        content = {"env": "not a list"}
        path = writeFile(tmp_path / "plugin.lock", json.dumps(content))

        metadata = PluginMetadata.loadJson(path)

        assert metadata is not None
        assert metadata.env == []


class TestLoadTomlMetadata:

    def test_missingFile(self, tmp_path):
        """ A missing pyproject.toml file yields None instead of raising. """
        assert PluginMetadata.loadToml(tmp_path / "pyproject.toml") is None

    def test_malformedToml(self, tmp_path):
        """ Malformed TOML content yields None instead of raising. """
        path = writeFile(tmp_path / "pyproject.toml", "not = [valid toml")
        assert PluginMetadata.loadToml(path) is None

    def test_fullProject(self, tmp_path):
        """
        "name"/"version"/"authors"/"description"/"license" come from "[project]", "publisher"/"env"/
        "requirements" from the Meshroom-specific "[tool.meshroom]" table.
        """
        content = (
            "[project]\n"
            "name = \"my-plugin\"\n"
            "version = \"1.2.3\"\n"
            "authors = [{ name = \"Alice\" }, \"Bob\"]\n"
            "description = \"A plugin that does things.\"\n"
            "license = \"MIT\"\n"
            "\n"
            "[tool.meshroom]\n"
            "publisher = \"my-publisher\"\n"
            "requirements = \"CUDA >= X.X\"\n"
            "env = [{ key = \"MY_VAR\", type = \"string\", value = \"myValue\" }]\n"
        )
        path = writeFile(tmp_path / "pyproject.toml", content)

        metadata = PluginMetadata.loadToml(path)

        assert metadata is not None
        assert metadata.name == "my-plugin"
        assert metadata.version == "1.2.3"
        assert metadata.publisher == "my-publisher"
        assert metadata.authors == ["Alice", "Bob"]
        assert metadata.description == "A plugin that does things."
        assert metadata.requirements == "CUDA >= X.X"
        assert metadata.license == "MIT"
        assert metadata.env == [{"key": "MY_VAR", "type": "string", "value": "myValue"}]

    def test_missingTablesFallBackToDefaults(self, tmp_path):
        """ A pyproject.toml with neither "[project]" nor "[tool.meshroom]" still parses. """
        path = writeFile(tmp_path / "pyproject.toml", "")

        metadata = PluginMetadata.loadToml(path)

        assert metadata is not None
        assert metadata.name is None
        assert metadata.version is None
        assert metadata.publisher is None
        assert metadata.authors == []
        assert metadata.description is None
        assert metadata.requirements is None
        assert metadata.license is None
        assert metadata.env == []

    def test_licenseDeclarations(self, tmp_path):
        """
        The license is the name declared by "license", else by the "License ::" classifiers, followed
        by the license files of "license.file" and "license-files".
        """
        writeFile(tmp_path / "LICENSE", "")
        writeFile(tmp_path / "NOTICE", "")
        mitClassifier = "classifiers = [\"License :: OSI Approved\", \"License :: OSI Approved :: MIT License\"]\n"
        declarations = {
            "license = \"MIT\"\n" + mitClassifier: "MIT",
            "license = { text = \"MIT License\\nCopyright\" }\n": "MIT License",
            mitClassifier: "MIT License",
            "license = { file = \"LICENSE\" }\n": "See file(s): LICENSE",
            "license-files = [\"LICEN[CS]E*\", \"NOTICE\", \"../LICENSE\"]\n": "See file(s): LICENSE, NOTICE",
            "license = \"MIT\"\nlicense-files = [\"LICENSE\"]\n": "MIT (see file(s): LICENSE)",
            mitClassifier + "license = { file = \"LICENSE\" }\n": "MIT License (see file(s): LICENSE)",
            "license = 42\nlicense-files = \"LICENSE\"\n": None,
        }
        for declaration, expected in declarations.items():
            path = writeFile(tmp_path / "pyproject.toml", "[project]\n" + declaration)
            assert PluginMetadata.loadToml(path).license == expected, declaration


class TestAssets:

    SHA256 = "a" * 64

    def test_toml(self, tmp_path):
        """ "[[tool.meshroom.assets]]" entries are parsed into PluginAssets. """
        content = (
            "[[tool.meshroom.assets]]\n"
            "name = \"weights\"\n"
            "category = \"model\"\n"
            "url = \"https://example.com/weights.pt\"\n"
            "path = \"models/weights.pt\"\n"
            f"sha256 = \"{self.SHA256.upper()}\"\n"
        )
        path = writeFile(tmp_path / "pyproject.toml", content)

        metadata = PluginMetadata.loadToml(path)

        assert metadata.assets == [
            PluginAsset("weights", "model", "https://example.com/weights.pt", "models/weights.pt", self.SHA256)
        ]

    def test_json(self, tmp_path):
        """ "assets" entries of a JSON metadata file are parsed into PluginAssets. """
        content = {"assets": [{"name": "weights", "category": "model", "url": "https://example.com/weights.pt",
                               "path": "models/weights.pt"}]}
        path = writeFile(tmp_path / "config.json", json.dumps(content))

        metadata = PluginMetadata.loadJson(path)

        assert metadata.assets == [
            PluginAsset("weights", "model", "https://example.com/weights.pt", "models/weights.pt")
        ]

    def test_pathIsNormalized(self, tmp_path):
        """ An asset path is stored normalized, with POSIX separators. """
        content = {"assets": [{"name": "a", "category": "model", "url": "https://example.com/a.pt",
                               "path": "./models/./a.pt"}]}
        path = writeFile(tmp_path / "config.json", json.dumps(content))

        metadata = PluginMetadata.loadJson(path)

        assert [asset.path for asset in metadata.assets] == ["models/a.pt"]

    def test_invalidEntriesAreIgnored(self, tmp_path):
        """ Invalid asset entries are dropped, the valid ones are kept. """
        valid = {"name": "valid", "category": "model", "url": "https://example.com/valid.pt", "path": "valid.pt"}
        content = {"assets": [
            "notATable",
            {"category": "model", "url": "https://example.com/a.pt", "path": "a.pt"},
            {"name": "a", "url": "https://example.com/a.pt", "path": "a.pt"},
            {"name": "a", "category": 1, "url": "https://example.com/a.pt", "path": "a.pt"},
            {"name": "a", "category": "model", "path": "a.pt"},
            {"name": "a", "category": "model", "url": "https://example.com/a.pt"},
            {"name": "-a", "category": "model", "url": "https://example.com/a.pt", "path": "a.pt"},
            {"name": "a", "category": "model", "url": "https://example.com/a.pt", "path": "/abs/a.pt"},
            {"name": "a", "category": "model", "url": "https://example.com/a.pt", "path": "C:/a.pt"},
            {"name": "a", "category": "model", "url": "https://example.com/a.pt", "path": "../a.pt"},
            {"name": "a", "category": "model", "url": "https://example.com/a.pt", "path": ""},
            {"name": "a", "category": "model", "url": "https://example.com/a.pt", "path": "a.pt", "sha256": "notASha"},
            valid,
            dict(valid, path="other.pt"),
            dict(valid, name="other"),
        ]}
        path = writeFile(tmp_path / "config.json", json.dumps(content))

        metadata = PluginMetadata.loadJson(path)

        assert metadata.assets == [PluginAsset("valid", "model", "https://example.com/valid.pt", "valid.pt")]

    def test_nonListAssetsAreIgnored(self, tmp_path):
        """ A non-list "assets" value is dropped as a whole. """
        path = writeFile(tmp_path / "config.json", json.dumps({"assets": {"name": "a"}}))
        assert PluginMetadata.loadJson(path).assets == []

    def test_resolvePath(self, tmp_path):
        """ An asset path is resolved relative to the plugin folder. """
        asset = PluginAsset("a", "model", "https://example.com/a.pt", "models/a.pt")
        assert asset.resolvePath(tmp_path) == tmp_path / "models" / "a.pt"


class TestResolveEnv:

    def test_plainStringValue(self, tmp_path):
        """ A "string"-typed (or untyped) entry is kept as-is. """
        metadata = PluginMetadata(env=[{"key": "MY_VAR", "type": "string", "value": "myValue"}])

        resolved = metadata.resolveEnv(tmp_path)

        assert resolved == {"MY_VAR": "myValue"}

    def test_existingRelativePathIsResolved(self, tmp_path):
        """ A "path"-typed entry pointing to an existing relative path is resolved and posix-ified. """
        (tmp_path / "sub").mkdir()
        metadata = PluginMetadata(env=[{"key": "MY_PATH", "type": "path", "value": "sub"}])

        resolved = metadata.resolveEnv(tmp_path)

        assert resolved == {"MY_PATH": (tmp_path / "sub").resolve().as_posix()}

    def test_nonExistingPathIsKeptUnresolved(self, tmp_path):
        """ A "path"-typed entry pointing nowhere is kept as its original, unresolved value. """
        metadata = PluginMetadata(env=[{"key": "MY_PATH", "type": "path", "value": "does/not/exist"}])

        resolved = metadata.resolveEnv(tmp_path)

        assert resolved == {"MY_PATH": "does/not/exist"}

    def test_entryMissingKeyOrValueIsSkipped(self, tmp_path):
        """ Entries missing "key" or "value" are skipped rather than raising. """
        metadata = PluginMetadata(env=[
            {"type": "string", "value": "noKey"},
            {"key": "NO_VALUE", "type": "string"},
            {"key": "MY_VAR", "type": "string", "value": "myValue"},
        ])

        resolved = metadata.resolveEnv(tmp_path)

        assert resolved == {"MY_VAR": "myValue"}


class TestLockfile:

    def test_writeRead(self, tmp_path):
        """ A lockfile written by "writeLockfile" is read back identically by "loadJson". """
        metadata = PluginMetadata(
            name="my-plugin",
            version="1.2.3",
            publisher="my-publisher",
            authors=["Alice"],
            description="A plugin that does things.",
            requirements="CUDA >= X.X",
            license="MIT (see file(s): LICENSE)",
            env=[{"key": "MY_VAR", "type": "string", "value": "myValue"}],
            assets=[PluginAsset("weights", "model", "https://example.com/weights.pt", "models/weights.pt", "a" * 64)],
        )
        lockfilePath = tmp_path / "plugin.lock"

        metadata.writeLockfile(lockfilePath)
        reloaded = PluginMetadata.loadJson(lockfilePath)

        assert reloaded is not None
        assert reloaded.name == metadata.name
        assert reloaded.version == metadata.version
        assert reloaded.publisher == metadata.publisher
        assert reloaded.authors == metadata.authors
        assert reloaded.description == metadata.description
        assert reloaded.requirements == metadata.requirements
        assert reloaded.license == metadata.license
        assert reloaded.env == metadata.env
        assert reloaded.assets == metadata.assets
