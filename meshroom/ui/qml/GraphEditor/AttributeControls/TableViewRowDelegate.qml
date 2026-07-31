import QtQuick
import QtQuick.Controls

Item {
    id: root
    property int rowIndex: 0
    property var rowObject: null
    property real rowHeight: 24
    property real tableWidth: 100
    property var scaledColumnWidths: []
    property bool editable: true
    property var appPalette: palette
    signal rowResized(int rowIndex, real newHeight)
    width: tableWidth
    height: rowHeight
    Row {
        spacing: 1
        anchors.fill: parent
        Repeater {
            model: root.rowObject && root.rowObject.value
                   ? root.rowObject.value.count
                   : 0
            delegate: TableViewCellDelegate {
                cellIndex: index
                rowObject: root.rowObject
                rowIndex: root.rowIndex
                cellWidth: (root.scaledColumnWidths && root.scaledColumnWidths.length > index)
                           ? root.scaledColumnWidths[index]
                           : 100
                cellHeight: root.height
            }
        }
    }
    MouseArea {
        id: colResizeHandle
        width: parent.width
        height: 6
        anchors.bottom: parent.bottom
        cursorShape: Qt.SizeVerCursor
        preventStealing: true
        property real lastY: 0
        onPressed: function(mouse) {
            colResizeHandle.grabMouse()
            lastY = mapToGlobal(mouse.x, mouse.y).y
        }
        onReleased: function(mouse) { colResizeHandle.ungrabMouse() }
        onPositionChanged: function(mouse) {
            if (!pressed)
                return
            var globalY = mapToGlobal(mouse.x, mouse.y).y
            var delta = globalY - lastY
            lastY = globalY
            root.rowResized(root.rowIndex, Math.max(20, root.rowHeight + delta))
        }
    }
}
