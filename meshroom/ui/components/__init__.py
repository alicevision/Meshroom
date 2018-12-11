
def registerTypes():
    from PySide2.QtQml import qmlRegisterType
    from meshroom.ui.components.edge import EdgeMouseArea
    from meshroom.ui.components.filepath import FilepathHelper
    from meshroom.ui.components.scene3D import Scene3DHelper, TrackballController

    qmlRegisterType(EdgeMouseArea, "GraphEditor", 1, 0, "EdgeMouseArea")
    qmlRegisterType(FilepathHelper, "Meshroom.Helpers", 1, 0, "FilepathHelper")  # TODO: uncreatable
    qmlRegisterType(Scene3DHelper, "Meshroom.Helpers", 1, 0, "Scene3DHelper")  # TODO: uncreatable
    qmlRegisterType(TrackballController, "Meshroom.Helpers", 1, 0, "TrackballController")
