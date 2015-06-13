import QtQuick 2.2
import QtQuick.Layouts 1.1

import "../components/headers"

Item {
    property Component body: Item {}

    // body
    Loader {
        anchors.fill: parent
        sourceComponent: body
    }
}
