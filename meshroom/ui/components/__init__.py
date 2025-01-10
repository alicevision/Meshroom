
def registerTypes():
    from PySide6.QtQml import qmlRegisterType, qmlRegisterSingletonType
    from meshroom.ui.components.clipboard import ClipboardHelper
    from meshroom.ui.components.edge import EdgeMouseArea
    from meshroom.ui.components.filepath import FilepathHelper
    from meshroom.ui.components.scene3D import Scene3DHelper, TrackballController, Transformations3DHelper
    from meshroom.ui.components.csvData import CsvData
    from meshroom.ui.components.geom2D import Geom2D
    from meshroom.ui.components.scriptEditor import PySyntaxHighlighter

    qmlRegisterType(EdgeMouseArea, "GraphEditor", 1, 0, "EdgeMouseArea")
    qmlRegisterType(ClipboardHelper, "Meshroom.Helpers", 1, 0, "ClipboardHelper")  # TODO: uncreatable
    qmlRegisterType(FilepathHelper, "Meshroom.Helpers", 1, 0, "FilepathHelper")  # TODO: uncreatable
    qmlRegisterType(Scene3DHelper, "Meshroom.Helpers", 1, 0, "Scene3DHelper")  # TODO: uncreatable
    qmlRegisterType(Transformations3DHelper, "Meshroom.Helpers", 1, 0, "Transformations3DHelper")  # TODO: uncreatable
    qmlRegisterType(TrackballController, "Meshroom.Helpers", 1, 0, "TrackballController")
    qmlRegisterType(CsvData, "DataObjects", 1, 0, "CsvData")
    qmlRegisterType(PySyntaxHighlighter, "ScriptEditor", 1, 0, "PySyntaxHighlighter")

    qmlRegisterSingletonType(Geom2D, "Meshroom.Helpers", 1, 0, "Geom2D")
