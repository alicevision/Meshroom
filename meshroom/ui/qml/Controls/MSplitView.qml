import QtQuick 2.15
import QtQuick.Controls 2.15

SplitView {
    id: splitView

    handle: Item {
        id: handleDelegate
        implicitWidth: 5
        implicitHeight: 5
        property bool hovered: SplitHandle.hovered
        property bool pressed: SplitHandle.pressed
        Rectangle {
            id: handleDisplay
            anchors.centerIn: parent
            property int handleSize: handleDelegate.hovered ? 3 : 1
            width: splitView.orientation === Qt.Horizontal ? handleSize : handleDelegate.width
            height: splitView.orientation === Qt.Vertical ? handleSize : handleDelegate.height
            color: handleDelegate.pressed ? Qt.lighter(palette.highlight, 1.5)
                : (handleDelegate.hovered ? palette.highlight : palette.base)
        }
    }
}
