import QtQuick
import QtQuick.Controls

Item {
    id: root
    property int rowIndex: 0
    property var rowObject: null
    property real rowHeight: 24
    property real tableWidth: 100
    property var scaledColumnWidths: []
    readonly property var maxColumnWidths: {
        var result = []
        for (var i = 0; i < cellRepeater.count; i++) {
            var item = cellRepeater.itemAt(i)
            result.push(item ? item.maxCellWidth : Infinity)
        }
        return result
    }
    property bool editable: true
    property var appPalette: palette
    readonly property var minColumnWidths: {
    var result = []
        for (var i = 0; i < cellRepeater.count; i++) {
            var cellItem = cellRepeater.itemAt(i)
            result.push(cellItem ? cellItem.minCellWidth : 60)
        }
    return result
}
    width: tableWidth
    height: rowHeight
    Row {
        spacing: 1
        anchors.fill: parent
        Repeater {
            id: cellRepeater
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
                maxWidth: (root.maxColumnWidths && root.maxColumnWidths.length > index)
                          ? root.maxColumnWidths[index]
                          : 100
            }
        }
    }
}
