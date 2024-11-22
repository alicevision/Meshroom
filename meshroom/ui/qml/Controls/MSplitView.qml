import QtQuick
import QtQuick.Controls

SplitView {
    id: splitView

    handle: Rectangle {
        id: handleDelegate
        implicitWidth: 5
        implicitHeight: 5
        color: palette.window
        property bool hovered: SplitHandle.hovered
        property bool pressed: SplitHandle.pressed
        Rectangle {
            id: handleDisplay
            anchors.centerIn: parent
            property int handleSize: handleDelegate.pressed ? 3 : 1
            width: splitView.orientation === Qt.Horizontal ? handleSize : handleDelegate.width
            height: splitView.orientation === Qt.Vertical ? handleSize : handleDelegate.height
            color: handleDelegate.hovered ? palette.highlight : palette.base
        }
    }
}
