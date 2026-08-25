import json

import meshroom.core
from meshroom.core.files import (
    MESHROOM_PROJECT_EXTENSION,
    MESHROOM_TEMPLATE_EXTENSION,
    isTemplateFile,
    withExtension,
)
from meshroom.core.graph import Graph
from meshroom.core.plugins.base import Plugin


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
    explicit_template_file = tmp_path / f"explicit{MESHROOM_TEMPLATE_EXTENSION}"
    legacy_template_file = tmp_path / f"legacy{MESHROOM_PROJECT_EXTENSION}"
    project_file = tmp_path / f"project{MESHROOM_PROJECT_EXTENSION}"

    write_graph_file(explicit_template_file, template=True)
    write_graph_file(legacy_template_file, template=True)
    write_graph_file(project_file, template=False)

    plugin = Plugin("testPlugin", str(tmp_path))

    assert plugin.templates == {
        "explicit": str(explicit_template_file),
        "legacy": str(legacy_template_file),
    }
