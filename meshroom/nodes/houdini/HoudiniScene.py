__version__ = "1.0"

from meshroom.core import desc


class HoudiniScene(desc.LiveNode):
    """
    The Houdini scene the subgraph works on, the value that prevails:
    - in a Meshroom task (Compute, farm, Run Live): opens "Scene File" (unless it is already open), e.g.
      the path found by a pipeline node such as GetCgScene;
    - in a Houdini session (meshroom.subgraph.run from the Python shell): the open scene; "Scene File" is
      not read, so the nodes only computing it are not run. With "In Houdini Session" set to "sceneFile",
      "Scene File" is computed and opened there too (Houdini asks to save the changes of the open scene).
    Its output is the path of the scene, to connect to the "scene" input of the next Houdini nodes.
    """
    category = "Houdini"
    context = "houdini"

    inputs = [
        desc.File(
            name="hipFile",
            label="Scene File",
            description="Scene to open in a Meshroom task (ignored in a Houdini session, where the open scene is used).",
            value="",
        ),
        desc.ChoiceParam(
            name="inSession",
            label="In Houdini Session",
            description="Scene used when the subgraph runs in an open Houdini session:\n"
                        " - openScene: the open scene (the nodes computing Scene File are not run).\n"
                        " - sceneFile: Scene File, opened if it is not the open scene.",
            value="openScene",
            values=["openScene", "sceneFile"],
        ),
    ]

    outputs = [
        desc.File(
            name="scene",
            label="Scene",
            description="Path of the scene, to connect to the next Houdini nodes.",
            value=None,
        ),
    ]

    @classmethod
    def ignoredInputs(cls, node, ctx):
        if ctx.context.ownsSession or node.inSession.value == "sceneFile":
            return ()
        return ("hipFile",)

    def execute(self, ctx, inputs):
        session = ctx.context
        if (session.ownsSession or inputs.get("inSession") == "sceneFile") and inputs.get("hipFile"):
            ctx.logger.info(f"[{ctx.nodeName}] Scene: {inputs['hipFile']}")
            session.loadScene(inputs["hipFile"])
        return {"scene": session.session.hipFile.path()}
