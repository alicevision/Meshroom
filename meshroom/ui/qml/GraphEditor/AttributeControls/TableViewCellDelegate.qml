import QtQuick
import QtQuick.Controls

Rectangle {
    id: cellRect
    property int cellIndex: 0
    property var rowObject: null
    property int rowIndex: 0
    property real cellWidth: 100
    property real cellHeight: 24
    property bool editable: true
    property bool cellReady: false
    property real minCellWidth: 60
    signal loaderReady()
    width: cellWidth
    height: cellHeight
    color: palette.window
    border.color: palette.mid
    clip: true
    property var cell: rowObject
                       ? rowObject.value.at(cellIndex)
                       : null
    Rectangle {
        anchors.centerIn: parent
        width: valueEditor.width + 8
        height: valueEditor.height + 4
        radius: 3
        color: palette.base
        visible: cellRect.cell &&
                 (cellRect.cell.type === "BoolParam" ||
                  cellRect.cell.type === "ChoiceParam")
    }
    AttributeValueEditor {
        id: valueEditor
        property bool isCheckbox: attribute && attribute.type === "BoolParam"
        anchors.fill: isCheckbox ? undefined : parent
        anchors.centerIn: isCheckbox ? parent : undefined
        attribute: cellRect.cell
        editable: cellRect.editable
        onStatusChanged: {
            if (status !== Loader.Ready)
                return
            cellRect.minCellWidth = valueEditor.minWidth || 60
            cellRect.cellReady = true
            cellRect.loaderReady()
        }
    }
}

