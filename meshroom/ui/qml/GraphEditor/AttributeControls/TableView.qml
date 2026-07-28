import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import MaterialIcons 2.2
import Utils 1.0 

ColumnLayout {
    id: root
    spacing: 0
    property bool editable: true
    required property var attribute
    property var columnNames: {
        if (!attribute || !attribute.value || attribute.value.count === 0) return []
        var firstRow = attribute.value.at(0)
        if (!firstRow || !firstRow.value) return []
        var names = []
        for (var i = 0; i < firstRow.value.count; i++) {
            var child = firstRow.value.at(i)
            if (child) names.push(child.label)
        }
        return names
    }
    property var  columnWidths: []
    property var  rowHeights:   []
    property real totalTableWidth: {
        if (!columnWidths || columnWidths.length === 0) return 0
        var t = 0
        for (var i = 0; i < columnWidths.length; i++) t += columnWidths[i]
        t += Math.max(0, columnWidths.length - 1)
        return t
    }
    property real totalTableHeight: {
        if (!rowHeights || rowHeights.length === 0) return 0
        var t = 0
        for (var i = 0; i < rowHeights.length; i++) t += rowHeights[i]
        t += Math.max(0, rowHeights.length - 1)
        return t
    }
    property var  scaledColumnWidths: []
    property real scaledTableWidth:   0
    property var  scaledRowHeights:  []
    property real scaledTableHeight: 0
    property real availableW: outerFrame.width > 0 ? outerFrame.width  - fixedStrip.width  - vBar.width : 600
    property real availableH: outerFrame.height > 0 ? outerFrame.height - hBar.height : 400
    function updateScaledWidths() {
        if (!columnWidths || columnWidths.length === 0) {
            scaledColumnWidths = []
            scaledTableWidth   = 0
            return
        }
        var scaleFactor = Math.max(1.0, availableW / Math.max(totalTableWidth, 1))
        var result = []
        for (var i = 0; i < columnWidths.length; i++)
            result.push(columnWidths[i] * scaleFactor)
        scaledColumnWidths = result
        scaledTableWidth   = Math.max(totalTableWidth, availableW)
    }
    function updateScaledHeights() {
        if (!rowHeights || rowHeights.length === 0) {
            scaledRowHeights  = []
            scaledTableHeight = 0
            return
        }
        var scaleFactor = Math.max(1.0, availableH / Math.max(totalTableHeight, 1))
        var result = []
        for (var i = 0; i < rowHeights.length; i++)
            result.push(rowHeights[i] * scaleFactor)
        scaledRowHeights  = result
        scaledTableHeight = Math.max(totalTableHeight, availableH)
    }
    property bool expanded: false
    property var appPalette: palette
    RowLayout {
        spacing: 4
        ToolButton {
            text: root.expanded ? MaterialIcons.keyboard_arrow_down
                                       : MaterialIcons.keyboard_arrow_right
            font.family: MaterialIcons.fontFamily
            onClicked: root.expanded = !root.expanded
        }
        Label {
            Layout.alignment: Qt.AlignVCenter
            text: attribute.value.count + " elements"
        }
        ToolButton {
            text: MaterialIcons.add_circle_outline
            font.family: MaterialIcons.fontFamily
            font.pointSize: 11
            padding: 2
            enabled: root.editable
            onClicked: _currentScene.appendAttribute(attribute, undefined)
        }
        ToolButton {
            text: MaterialIcons.fullscreen
            font.family: MaterialIcons.fontFamily
            font.pointSize: 11
            padding: 2
            ToolTip.text: "Open in fullscreen"
            ToolTip.visible: hovered
            onClicked: {
                outerFrame.Layout.preferredWidth  = fullscreenWindow.width 
                outerFrame.Layout.preferredHeight = fullscreenWindow.height
                outerFrame.visible                = true
                outerFrame.parent  = fullscreenContent
                outerFrame.x       = 0
                outerFrame.y       = 0
                outerFrame.width   = Qt.binding(function() { return fullscreenWindow.width  })
                outerFrame.height  = Qt.binding(function() { return fullscreenWindow.height })
                outerFrame.isFullscreen = true
                fullscreenWindow.show()
            }
        }
    }
    Window {
        id: fullscreenWindow
        color: "#2d2d2d"
        width:  root.totalTableWidth  + 30 + 16 + 20
        height: root.totalTableHeight + 10 + 16 + 20
        title: attribute ? attribute.label : ""
        palette: root.appPalette
        Item {
            id: fullscreenContent
            anchors.fill: parent
        }
        onClosing: {
            outerFrame.width                  = undefined
            outerFrame.height                 = undefined
            outerFrame.Layout.preferredWidth  = -1
            outerFrame.parent                 = root
            outerFrame.isFullscreen           = false
            outerFrame.Layout.fillWidth       = true
            outerFrame.Layout.preferredHeight = Qt.binding(function() {
                return root.expanded
                    ? Math.min(root.totalTableHeight + 40, 330)
                    : 0
            })
            outerFrame.visible = Qt.binding(function() {
                return root.expanded
            })
        }
    }
    FontMetrics {
        id: fontMetrics
        font.bold: false
    }
    function initSizes() {
        var names = root.columnNames
        if (!names || names.length === 0) {
            root.columnWidths = []
            root.rowHeights   = []
            return
        }
        var widths = []
        for (var i = 0; i < names.length; i++)
            widths.push(fontMetrics.advanceWidth(names[i]) + 20)
        var heights = []
        if (attribute && attribute.value) {
            for (var r = 0; r < attribute.value.count; r++) {
                var rowAttr = attribute.value.at(r)
                if (!rowAttr || !rowAttr.value) continue
                for (var c = 0; c < rowAttr.value.count && c < widths.length; c++) {
                    var cell = rowAttr.value.at(c)
                    var cellText = cell ? String(cell.value) : ""
                    var cw = fontMetrics.advanceWidth(cellText) + 20
                    if (cw > widths[c]) widths[c] = cw
                }
                heights.push(30)
            }
        }
        root.columnWidths = widths
        root.rowHeights   = heights
    }
    Component.onCompleted: {
        root.initSizes()
    }
    Connections {
        target: attribute ? attribute.value : null
        function onCountChanged() {root.initSizes(); root.updateScaledWidths(); root.updateScaledHeights()}
        function onModelReset()   {root.initSizes(); root.updateScaledWidths(); root.updateScaledHeights()}
        function onRowsInserted() {root.initSizes(); root.updateScaledWidths(); root.updateScaledHeights()}
        function onDataChanged()  {root.initSizes(); root.updateScaledWidths(); root.updateScaledHeights()}
    }
    onAvailableWChanged: root.updateScaledWidths()
    onAvailableHChanged: root.updateScaledHeights()
    Item {
        id: outerFrame
        Layout.fillWidth: true
        visible: root.expanded
        Layout.preferredHeight: root.expanded
                                ? Math.min(root.totalTableHeight + 40, 330)
                                : 0
        property bool isFullscreen: false
        ScrollBar {
            id: hBar
            anchors.left:        fixedStrip.right
            anchors.right:       outerFrame.right
            anchors.bottom:      outerFrame.bottom
            anchors.rightMargin: vBar.width
            orientation:         Qt.Horizontal
            policy: flickable.contentWidth > flickable.width
                    ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
            size: Math.min(1.0, flickable.width / Math.max(flickable.contentWidth, 1))
            position: (flickable.contentX / Math.max(flickable.contentWidth - flickable.width, 1))
                      * (1.0 - size)
            onPositionChanged: {
                if (!pressed) return
                var maxPos = 1.0 - size
                var ratio  = maxPos > 0 ? position / maxPos : 0
                flickable.contentX = ratio * Math.max(flickable.contentWidth - flickable.width, 1)
            }
        }
        ScrollBar {
            id: vBar
            anchors.top:          outerFrame.top
            anchors.bottom:       outerFrame.bottom
            anchors.right:        outerFrame.right
            anchors.bottomMargin: hBar.height
            orientation:          Qt.Vertical
            policy: flickable.contentHeight > flickable.height
                    ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
            size: Math.min(1.0, flickable.height / Math.max(flickable.contentHeight, 1))
            position: (flickable.contentY / Math.max(flickable.contentHeight - flickable.height, 1))
                      * (1.0 - size)
            onPositionChanged: {
                if (!pressed) return
                var maxPos = 1.0 - size
                var ratio  = maxPos > 0 ? position / maxPos : 0
                flickable.contentY = ratio * Math.max(flickable.contentHeight - flickable.height, 1)
            }
        }
        Item {
            id: fixedHeader
            anchors.left:        fixedStrip.right
            anchors.right:       outerFrame.right
            anchors.top:         outerFrame.top
            anchors.rightMargin: vBar.width
            height: 30
            clip:   true
            Row {
                spacing: 1
                x: -flickable.contentX
                Repeater {
                    model: root.columnNames
                    delegate: Item {
                        id: headerCell
                        required property int    index
                        required property string modelData
                        width: root.scaledColumnWidths[index] || 100
                        height: 30
                        Rectangle {
                            anchors.fill: parent
                            color:        "#2d2d2d"
                            border.color: "#1d1d1d"
                            Text {
                                anchors.fill:        parent
                                text:                headerCell.modelData
                                color:               "#aaaaaa"
                                font.bold:           false
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment:   Text.AlignVCenter
                                elide:               Text.ElideRight
                            }
                        }
                        MouseArea {
                            width:  6
                            height: parent.height
                            anchors.right: parent.right
                            cursorShape:   Qt.SizeHorCursor
                            property real startX: 0
                            property real startW: 0
                            onPressed: function(mouse) {
                                grabMouse()
                                var p = mapToItem(root, mouse.x, mouse.y)
                                startX = p.x
                                startW = root.columnWidths[headerCell.index]
                            }
                            onReleased: function(mouse) {
                                ungrabMouse()
                            }
                            onPositionChanged: function(mouse) {
                                if (!pressed) return
                                var p    = mapToItem(root, mouse.x, mouse.y)
                                var newW = Math.max(40, startW + (p.x - startX))
                                var arr  = root.columnWidths.slice()
                                arr[headerCell.index] = newW
                                root.columnWidths = arr
                                root.updateScaledWidths()
                            }
                        }
                    }
                }
            }
        }
        Item {
            id: fixedStrip
            anchors.left:         outerFrame.left
            anchors.top:          outerFrame.top
            anchors.bottom:       outerFrame.bottom
            anchors.topMargin:    30
            anchors.bottomMargin: hBar.height
            width: 30
            clip:  true
            Column {
                spacing: 1
                width: parent.width
                y: -flickable.contentY
                Repeater {
                    model: attribute ? attribute.value : null
                    delegate: Item {
                        id: removeDelegate
                        required property int index
                        required property var object
                        width:  fixedStrip.width
                        height: root.scaledRowHeights[index] || 30
                        ToolButton {
                            anchors.centerIn: parent
                            enabled:          root.editable
                            text:             MaterialIcons.remove_circle_outline
                            font.family:      MaterialIcons.fontFamily
                            font.pointSize:   11
                            padding:          2
                            ToolTip.text:    "Remove Element"
                            ToolTip.visible: hovered
                            contentItem: Text {
                                text:                parent.text
                                font:                parent.font
                                color:               "#aaaaaa"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment:   Text.AlignVCenter
                            }
                            onClicked: _currentScene.removeAttribute(removeDelegate.object)
                        }
                    }
                }
            }
        }
        Item {
            id: cornerCell
            anchors.left:   outerFrame.left
            anchors.top:    outerFrame.top
            width:  fixedStrip.width
            height: fixedHeader.height
            visible: outerFrame.isFullscreen
            Rectangle {
                anchors.fill: parent
                color:        "#2d2d2d"
                border.color: "#1d1d1d"
            }
            ToolButton {
                anchors.centerIn: parent
                text:             MaterialIcons.add_circle_outline
                font.family:      MaterialIcons.fontFamily
                font.pointSize:   11
                padding:          2
                enabled:          root.editable
                ToolTip.text:    "Add Element"
                ToolTip.visible: hovered
                contentItem: Text {
                    text:                parent.text
                    font:                parent.font
                    color:               "#aaaaaa"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                }
                onClicked: _currentScene.appendAttribute(attribute, undefined)
            }
        }
        Flickable {
            id: flickable
            anchors.left:         fixedStrip.right
            anchors.top:          outerFrame.top
            anchors.right:        outerFrame.right
            anchors.bottom:       outerFrame.bottom
            anchors.topMargin:    30
            anchors.rightMargin:  vBar.width
            anchors.bottomMargin: hBar.height
            clip:          true
            contentWidth:  root.scaledTableWidth
            contentHeight: root.scaledTableHeight
            interactive:   true
            WheelHandler {
                onWheel: function(event) {
                    if (event.modifiers & Qt.ControlModifier) {
                        flickable.contentX = Math.max(0,
                            Math.min(flickable.contentWidth  - flickable.width,
                                     flickable.contentX - event.angleDelta.y / 120 * 40))
                    } else {
                        flickable.contentY = Math.max(0,
                            Math.min(flickable.contentHeight - flickable.height,
                                     flickable.contentY - event.angleDelta.y / 120 * 40))
                    }
                    event.accepted = true
                }
            }
            Column {
                spacing: 1
                Repeater {
                    id: rowRepeater
                    model: attribute ? attribute.value : null
                    delegate: TableViewRowDelegate {
                        rowIndex: index
                        rowObject: object
                        rowHeight: root.scaledRowHeights[index] || 30
                        tableWidth: root.scaledTableWidth
                        scaledColumnWidths: root.scaledColumnWidths
                        editable: root.editable
                        onRowResized: function(rowIndex, newH) {
                            var arr = root.rowHeights.slice()
                            arr[rowIndex] = newH
                            root.rowHeights = arr
                            root.updateScaledHeights()
                        }
                    }
                }
            }
        }
    }
}
