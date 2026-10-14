import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * CurveListDelegate is a row of the CurveList: color, name, value at the playhead and curve actions.
 */

Item {
    id: root

    // Rows of a collapsed group are hidden
    implicitHeight: collapsed ? 0 : 24
    visible: !collapsed

    required property int index
    required property string curveName
    required property color curveColor
    required property bool curveVisible
    required property string curveGroup

    property bool collapsed: false

    property var curveModel
    property var viewer

    readonly property bool isCurrent: viewer.currentIndex === index
    readonly property real playheadValue: {
        const value = viewer.playheadValues[index]
        return typeof value === "number" ? value : NaN
    }

    Rectangle {
        anchors.fill: parent
        color: root.isCurrent ? Qt.rgba(palette.highlight.r, palette.highlight.g, palette.highlight.b, 0.3)
             : mouseArea.containsMouse ? Qt.lighter(palette.window, 1.15)
             : "transparent"
    }

    MouseArea {
        id: mouseArea

        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.viewer.currentIndex = root.isCurrent ? -1 : root.index
        onDoubleClicked: {
            root.viewer.currentIndex = root.index
            root.viewer.fitCurve(root.index)
        }
    }

    RowLayout {
        anchors.fill: parent
        // Indent the curves of a group under its header
        anchors.leftMargin: root.curveGroup ? 22 : 6
        spacing: 4

        Rectangle {
            implicitWidth: 10
            implicitHeight: 10
            radius: 2
            color: root.curveVisible ? root.curveColor : "transparent"
            border.color: root.curveColor
        }

        Label {
            Layout.fillWidth: true
            text: root.curveName
            elide: Text.ElideRight
            color: root.curveVisible ? palette.text : palette.disabled.text
            font.bold: root.isCurrent
        }

        Label {
            text: isNaN(root.playheadValue) ? "-" : root.playheadValue.toPrecision(5)
            color: root.curveVisible ? palette.text : palette.disabled.text
            font.pointSize: 8
            font.family: "monospace"
            opacity: 0.8
        }

        MaterialToolButton {
            text: MaterialIcons.swap_horiz
            font.pointSize: 10
            padding: 2
            focusPolicy: Qt.NoFocus
            ToolTip.text: "Fit Horizontally"
            onClicked: root.viewer.fitCurveHorizontally(root.index)
        }
        MaterialToolButton {
            text: MaterialIcons.swap_vert
            font.pointSize: 10
            padding: 2
            focusPolicy: Qt.NoFocus
            ToolTip.text: "Fit Vertically"
            onClicked: root.viewer.fitCurveVertically(root.index)
        }
        MaterialToolButton {
            text: root.curveVisible ? MaterialIcons.visibility : MaterialIcons.visibility_off
            font.pointSize: 10
            padding: 2
            focusPolicy: Qt.NoFocus
            ToolTip.text: root.curveVisible ? "Hide" : "Show"
            onClicked: root.curveModel.setVisible(root.index, !root.curveVisible)
        }
        MaterialToolButton {
            text: MaterialIcons.delete_
            font.pointSize: 10
            padding: 2
            focusPolicy: Qt.NoFocus
            ToolTip.text: "Remove"
            onClicked: root.curveModel.removeCurve(root.index)
        }
    }
}
