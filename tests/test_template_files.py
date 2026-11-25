import json
from contextlib import contextmanager

import pytest

import meshroom.core
from meshroom.core.files import (
    MESHROOM_PROJECT_EXTENSION,
    MESHROOM_TEMPLATE_EXTENSION,
    isTemplateFile,
    withExtension,
)
from meshroom.core import pluginManager
from meshroom.core.graph import Graph
from meshroom.core.graphIO import getTemplateInfo
from .utils import registeredPlugin


def write_graph_file(path, template=False):
    path.write_text(
        json.dumps(
            {
                "header": {
                    "fileVersion": "2.1",
                    "template": template,
                },
                "graph": {},
            }
        )
    )


def test_template_file_detection_from_extension_and_legacy_metadata(tmp_path):
    project_file = tmp_path / f"project{MESHROOM_PROJECT_EXTENSION}"
    legacy_template_file = tmp_path / f"legacy{MESHROOM_PROJECT_EXTENSION}"
    explicit_template_file = tmp_path / f"template{MESHROOM_TEMPLATE_EXTENSION}"

    write_graph_file(project_file, template=False)
    write_graph_file(legacy_template_file, template=True)
    write_graph_file(explicit_template_file, template=False)

    assert not isTemplateFile(project_file)
    assert isTemplateFile(legacy_template_file)
    assert isTemplateFile(explicit_template_file)


def test_template_initialization_does_not_bind_filepath(tmp_path):
    template_file = tmp_path / f"template{MESHROOM_TEMPLATE_EXTENSION}"
    graph = Graph("Template")
    graph.save(template_file, setupProjectFile=False, template=True)

    loaded_graph = Graph("")
    loaded_graph.initFromTemplate(template_file, keepOutputNodes=True)

    assert loaded_graph.filepath == ""


def test_template_extension_is_appended_for_template_saves():
    assert withExtension("template", MESHROOM_TEMPLATE_EXTENSION) == f"template{MESHROOM_TEMPLATE_EXTENSION}"
    assert (
        withExtension(f"template{MESHROOM_TEMPLATE_EXTENSION}", MESHROOM_TEMPLATE_EXTENSION)
        == f"template{MESHROOM_TEMPLATE_EXTENSION}"
    )
    assert (
        withExtension(f"template{MESHROOM_PROJECT_EXTENSION}", MESHROOM_TEMPLATE_EXTENSION)
        == f"template{MESHROOM_PROJECT_EXTENSION}{MESHROOM_TEMPLATE_EXTENSION}"
    )


def test_pipeline_template_discovery_supports_mgt_and_legacy_mg_metadata(tmp_path):
    explicit_template_file = tmp_path / f"explicit{MESHROOM_TEMPLATE_EXTENSION}"
    legacy_template_file = tmp_path / f"legacy{MESHROOM_PROJECT_EXTENSION}"
    project_file = tmp_path / f"project{MESHROOM_PROJECT_EXTENSION}"

    write_graph_file(explicit_template_file, template=True)
    write_graph_file(legacy_template_file, template=True)
    write_graph_file(project_file, template=False)

    previous_templates = dict(meshroom.core.pipelineTemplates)
    try:
        meshroom.core.pipelineTemplates.clear()
        meshroom.core.loadPipelineTemplates(str(tmp_path))

        assert meshroom.core.pipelineTemplates == {
            "explicit": str(explicit_template_file),
            "legacy": str(legacy_template_file),
        }
    finally:
        meshroom.core.pipelineTemplates.clear()
        meshroom.core.pipelineTemplates.update(previous_templates)


def test_plugin_template_discovery_supports_mgt_and_legacy_mg_metadata(tmp_path):
    meshroom_folder_path = tmp_path / "meshroom"
    meshroom_folder_path.mkdir()
    explicit_template_file = meshroom_folder_path / f"explicit{MESHROOM_TEMPLATE_EXTENSION}"
    legacy_template_file = meshroom_folder_path / f"legacy{MESHROOM_PROJECT_EXTENSION}"
    project_file = meshroom_folder_path / f"project{MESHROOM_PROJECT_EXTENSION}"

    write_graph_file(explicit_template_file, template=True)
    write_graph_file(legacy_template_file, template=True)
    write_graph_file(project_file, template=False)

    with registeredPlugin("testTemplatePlugin", str(tmp_path)):
        plugin = pluginManager.getPlugin("testTemplatePlugin")
        assert plugin.templates == {
            "explicit": str(explicit_template_file),
            "legacy": str(legacy_template_file),
        }


def save_versioned_template(path):
    graph = Graph("Template")
    node = graph.addNewNode("AllAttributesNode")
    graph.save(path, setupProjectFile=False, template=True)
    return json.loads(path.read_text()), node.name


def test_template_version_check_reads_node_versions(tmp_path):
    from meshroom.core.test import checkTemplateVersions

    template_file = tmp_path / f"template{MESHROOM_TEMPLATE_EXTENSION}"
    file_data, node_name = save_versioned_template(template_file)
    assert "nodesVersions" not in file_data["header"]
    assert checkTemplateVersions(str(template_file), nodesAlreadyLoaded=True)

    file_data["graph"][node_name]["version"] = "2.0"
    template_file.write_text(json.dumps(file_data))
    assert not checkTemplateVersions(str(template_file), nodesAlreadyLoaded=True)


def test_template_version_check_falls_back_to_legacy_header(tmp_path):
    from meshroom.core.test import checkTemplateVersions

    template_file = tmp_path / f"template{MESHROOM_TEMPLATE_EXTENSION}"
    file_data, node_name = save_versioned_template(template_file)
    del file_data["graph"][node_name]["version"]
    file_data["header"]["fileVersion"] = "2.1"
    file_data["header"]["nodesVersions"] = {"AllAttributesNode": "2.0"}
    template_file.write_text(json.dumps(file_data))

    assert not checkTemplateVersions(str(template_file), nodesAlreadyLoaded=True)


def test_template_info_is_kept_on_template_saves(tmp_path):
    template_file = tmp_path / f"template{MESHROOM_TEMPLATE_EXTENSION}"
    graph = Graph("Template")
    graph.header["templateInfo"] = {"category": "Photogrammetry", "icon": "camera"}
    graph.save(template_file, setupProjectFile=False, template=True)

    resaved_file = tmp_path / f"resaved{MESHROOM_TEMPLATE_EXTENSION}"
    loaded_graph = Graph("")
    loaded_graph.initFromTemplate(template_file)
    loaded_graph.save(resaved_file, setupProjectFile=False, template=True)

    header = json.loads(resaved_file.read_text())["header"]
    assert header["templateInfo"] == {"category": "Photogrammetry", "icon": "camera"}
    assert "sourceTemplate" not in header


@contextmanager
def registeredTemplates(folder):
    """ Register only the pipeline templates of `folder` while in the context. """
    previousTemplates = dict(meshroom.core.pipelineTemplates)
    meshroom.core.pipelineTemplates.clear()
    try:
        meshroom.core.loadPipelineTemplates(str(folder))
        yield
    finally:
        meshroom.core.pipelineTemplates.clear()
        meshroom.core.pipelineTemplates.update(previousTemplates)


def test_project_records_its_source_template(tmp_path):
    template_file = tmp_path / f"myTemplate{MESHROOM_TEMPLATE_EXTENSION}"
    graph = Graph("Template")
    graph.header["templateInfo"] = {"category": "Utilities"}
    graph.save(template_file, setupProjectFile=False, template=True)
    project_file = tmp_path / f"project{MESHROOM_PROJECT_EXTENSION}"

    with registeredTemplates(tmp_path):
        project = Graph("")
        project.initFromTemplate(template_file)
        project.save(project_file)

        header = json.loads(project_file.read_text())["header"]
        assert header["sourceTemplate"] == {"name": "myTemplate", "plugin": None}
        assert "templateInfo" not in header

        # The source template is kept when re-saving the loaded project
        reloaded = Graph("")
        reloaded.load(project_file)
        reloaded.save()
        assert json.loads(project_file.read_text())["header"]["sourceTemplate"] == header["sourceTemplate"]

        # Metadata is resolved from the registered template at read time
        assert getTemplateInfo("myTemplate") == {"category": "Utilities"}
    assert getTemplateInfo("myTemplate") == {}


def test_unregistered_file_is_not_recorded_as_source_template(tmp_path):
    # Same name as a registered template, but another file
    template_file = tmp_path / f"myTemplate{MESHROOM_TEMPLATE_EXTENSION}"
    Graph("Template").save(template_file, setupProjectFile=False, template=True)
    registered_folder = tmp_path / "registered"
    registered_folder.mkdir()
    Graph("Template").save(registered_folder / template_file.name, setupProjectFile=False, template=True)

    # A project file opened as a template: its own source template is not kept either
    project_file = tmp_path / f"project{MESHROOM_PROJECT_EXTENSION}"
    project = Graph("")
    project.header["sourceTemplate"] = {"name": "myTemplate", "plugin": None}
    project.save(project_file)

    with registeredTemplates(registered_folder):
        for path in (template_file, project_file):
            graph = Graph("")
            graph.initFromTemplate(path)
            assert "sourceTemplate" not in graph.header


def test_project_records_the_plugin_of_its_source_template(tmp_path):
    meshroom_folder_path = tmp_path / "meshroom"
    meshroom_folder_path.mkdir()
    template_file = meshroom_folder_path / f"pluginTemplate{MESHROOM_TEMPLATE_EXTENSION}"
    graph = Graph("Template")
    graph.header["templateInfo"] = {"category": "HDR"}
    graph.save(template_file, setupProjectFile=False, template=True)

    with registeredPlugin("testSourceTemplatePlugin", str(tmp_path)):
        project = Graph("")
        project.initFromTemplate(str(template_file))
        source = project.header["sourceTemplate"]
        assert source == {"name": "pluginTemplate", "plugin": "testSourceTemplatePlugin"}
        assert getTemplateInfo(source["name"], source["plugin"]) == {"category": "HDR"}


def test_set_template_info_is_saved_with_the_template(tmp_path):
    template_file = tmp_path / f"template{MESHROOM_TEMPLATE_EXTENSION}"
    graph = Graph("Template")
    assert graph.templateInfo == {}

    graph.setTemplateInfo({"label": "My Template", "icon": "camera"})
    assert graph.templateInfo == {"label": "My Template", "icon": "camera"}
    graph.save(template_file, setupProjectFile=False, template=True)
    assert json.loads(template_file.read_text())["header"]["templateInfo"] == {"label": "My Template", "icon": "camera"}

    # An empty info removes it from the template
    graph.setTemplateInfo({})
    assert graph.templateInfo == {}
    graph.save(template_file, setupProjectFile=False, template=True)
    assert "templateInfo" not in json.loads(template_file.read_text())["header"]

    # The returned info is a copy: editing it does not change the graph
    graph.setTemplateInfo({"category": "Utilities"})
    graph.templateInfo["category"] = "Other"
    assert graph.templateInfo == {"category": "Utilities"}


def test_invalid_template_info_is_reported_and_kept(tmp_path):
    template_file = tmp_path / f"badInfo{MESHROOM_TEMPLATE_EXTENSION}"
    Graph("Template").save(template_file, setupProjectFile=False, template=True)
    data = json.loads(template_file.read_text())
    data["header"]["templateInfo"] = "HDR"
    template_file.write_text(json.dumps(data))

    with registeredTemplates(tmp_path):
        with pytest.raises(ValueError, match="badInfo"):
            getTemplateInfo("badInfo")

    graph = Graph("")
    graph.initFromTemplate(template_file)
    with pytest.raises(ValueError, match="templateInfo"):
        graph.templateInfo
    # The invalid metadata is neither overwritten nor removed, so that the user can fix it in the file
    with pytest.raises(ValueError):
        graph.setTemplateInfo({"category": "HDR"})
    with pytest.raises(ValueError):
        graph.setTemplateInfo({})
    graph.save(template_file, setupProjectFile=False, template=True)
    assert json.loads(template_file.read_text())["header"]["templateInfo"] == "HDR"
