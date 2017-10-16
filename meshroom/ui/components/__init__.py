
def registerTypes():
    from PySide2.QtQml import qmlRegisterType
    from meshroom.ui.components.edge import EdgeMouseArea

    qmlRegisterType(EdgeMouseArea, "GraphEditor", 1, 0, "EdgeMouseArea")
