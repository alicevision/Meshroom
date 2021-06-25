import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2
import MaterialIcons 2.2
import Utils 1.0

ListView {
    id: root
    property bool readOnly: false
    property int labelWidth: 180

    signal upgradeRequest()
    signal attributeDoubleClicked(var mouse, var attribute)

    implicitHeight: contentHeight

    spacing: 2
    clip: true
    ScrollBar.vertical: ScrollBar { id: scrollBar }

    delegate: Loader {
        active: object.enabled && (!object.desc.advanced)
        visible: active
        height: item ? item.implicitHeight : -spacing // compensate for spacing if item is hidden

        sourceComponent: ImageIntrinsicDelegate {
            width: root.width - scrollBar.width
            readOnly: root.readOnly
            attribute: object
        }
    }

    // Helper MouseArea to lose edit/activeFocus
    // when clicking on the background
    MouseArea {
        anchors.fill: parent
        onClicked: root.forceActiveFocus()
        z: -1
    }
}
