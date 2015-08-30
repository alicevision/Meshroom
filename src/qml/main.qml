import QtQuick 2.2
import QtQuick.Controls 1.3

import "pages"
import "styles"

ApplicationWindow {

    id: _mainWindow
    width: 800
    height: 800
    visible: true
    style: _style.bggl

    DefaultStyle {
        id: _style
    }
    Loader {
        anchors.fill: parent
        objectName: "instanCodingLoader"
        source: "pages/IndexPage.qml"
    }
}
