import QtQuick 2.2
import QtQuick.Controls 1.3

import "styles"

ApplicationWindow {

    id: _mainWindow

    width: 800
    height: 800
    visible: true
    style: _style.bggl

    // main application style sheet
    DefaultStyle {
        id: _style
    }

    // main loader, needed to enable instant coding
    Loader {
        id: _mainLoader
        anchors.fill: parent
        objectName: "instanCodingLoader"
        source: "IndexPage.qml"
    }
}
