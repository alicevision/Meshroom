import QtQuick
import QtQuick.Controls

Item {
    id: rowRoot
    property int rowIndex: 0
    property var rowObject: null
    property real rowHeight: 24
    property real tableWidth: 100
    property var scaledColumnWidths: []
    property bool editable: true
    property var minColumnWidths: []
    width: tableWidth
    height: rowHeight
    Row {
        spacing: 1
        anchors.fill: parent
        Repeater {
            id: cellRepeater
            model: rowRoot.rowObject && rowRoot.rowObject.value
                   ? rowRoot.rowObject.value.count
                   : 0
            onItemAdded: function(index, item) {
                rowRoot.refreshColumnWidths()
            }
            delegate: TableViewCellDelegate {
                cellIndex: index
                rowObject: rowRoot.rowObject
                rowIndex: rowRoot.rowIndex
                cellWidth: (rowRoot.scaledColumnWidths &&
                              rowRoot.scaledColumnWidths.length > index)
                              ? rowRoot.scaledColumnWidths[index]
                              : 100
                cellHeight: rowRoot.rowHeight
                editable: rowRoot.editable
                onLoaderReady: {
                    rowRoot.refreshColumnWidths()
                }
            }
        }
    }
    function refreshColumnWidths() {
        var mins = []
        for (var i = 0; i < cellRepeater.count; i++) {
            var c = cellRepeater.itemAt(i)
            var ready = c && c.cellReady
            mins.push (ready ? c.minCellWidth : 60)
        }
        rowRoot.minColumnWidths = mins
    }
}
