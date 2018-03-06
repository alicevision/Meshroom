
def registerTypes():
    from PySide2.QtQml import qmlRegisterType
    from meshroom.ui.components.edge import EdgeMouseArea
    from meshroom.ui.components.filepath import FilepathHelper

    qmlRegisterType(EdgeMouseArea, "GraphEditor", 1, 0, "EdgeMouseArea")
    qmlRegisterType(FilepathHelper, "Meshroom.Helpers", 1, 0, "FilepathHelper")  # TODO: uncreatable

