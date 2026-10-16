"""
Bases of the scene nodes of the software contexts (HoudiniScene / HoudiniSave, MayaScene / MayaSave,
NukeScene / NukeSave in meshroom/nodes): the scene a subgraph works on, and its single save. They work with
any SceneContext (see contexts.py); a software only sets its context and its labels.
"""
from meshroom.core import desc


def sceneNodeInputs(software: str) -> list:
    return [
        desc.File(
            name="hipFile",
            label="Scene File",
            description=f"Scene to open in a Meshroom task (ignored in a {software} session, where the open scene is used).",
            value="",
        ),
        desc.ChoiceParam(
            name="inSession",
            label=f"In {software} Session",
            description=f"Scene used when the subgraph runs in an open {software} session:\n"
                        " - openScene: the open scene (the nodes computing Scene File are not run).\n"
                        " - sceneFile: Scene File, opened if it is not the open scene.",
            value="openScene",
            values=["openScene", "sceneFile"],
        ),
    ]


def sceneNodeOutputs() -> list:
    return [
        desc.File(
            name="scene",
            label="Scene",
            description="Path of the scene, to connect to the next nodes.",
            value=None,
        ),
    ]


def saveNodeInputs(software: str) -> list:
    return [
        desc.File(
            name="scene",
            label="Scene",
            description="Connect the previous node to run after it.",
            value="",
        ),
        desc.File(
            name="hipFile",
            label="Save As",
            description="Where to save the scene (empty: its current file).",
            value="",
        ),
        desc.BoolParam(
            name="saveInSession",
            label=f"Save In {software} Session",
            description=f"Also save when the subgraph runs in an open {software} session (from its Python shell).",
            value=False,
        ),
    ]


def saveNodeOutputs() -> list:
    return [
        desc.File(
            name="sceneOut",
            label="Scene",
            description="Path of the saved scene.",
            value=None,
        ),
    ]


class SceneNode(desc.LiveNode):
    """
    The scene the subgraph works on, the value that prevails:
    - in a Meshroom task (Compute, farm, Run Live): opens "Scene File" (unless it is already open), e.g.
      the path found by a pipeline node;
    - in a session of the software (meshroom.subgraph.run from its Python shell): the open scene; "Scene
      File" is not read, so the nodes only computing it are not run. With "In ... Session" set to
      "sceneFile", "Scene File" is computed and opened there too.
    """
    # Only depends on its inputs: not run again at each step of a loop
    runsEachStep = False

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
        return {"scene": session.currentScene()}


class SaveNode(desc.LiveNode):
    """
    Saves the scene once, with the changes of the previous nodes (the saves of the task nodes of the
    subgraph are grouped in this one). In a session of the software (meshroom.subgraph.run from its Python
    shell), the scene is only saved if "Save In ... Session" is on.
    """

    def execute(self, ctx, inputs):
        session = ctx.context
        if session.ownsSession or inputs.get("saveInSession"):
            session.saveScene(inputs.get("hipFile") or None)
            ctx.logger.info(f"[{ctx.nodeName}] Saved: {session.currentScene()}")
        else:
            session.discardPendingSave()
            ctx.logger.info(f"[{ctx.nodeName}] Session of the software: the scene is not saved.")
        return {"sceneOut": session.currentScene()}
