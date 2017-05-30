import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Templates 2.0 as T
import QtQuick.Layouts 1.1

import "."

T.ComboBox {

    id: control
    implicitWidth: 200
    implicitHeight: 30
    spacing: 10
    padding: 6

    background: Rectangle {
        color: Globals.window.color.dark
    }
    delegate: MenuItem {
        width: control.width
        text: control.textRole ? modelData[control.textRole] : modelData
        highlighted: control.highlightedIndex === index
    }
    contentItem: RowLayout {
        anchors.leftMargin: control.leftPadding
        anchors.rightMargin: control.rightPadding
        Label {
            id: text
            Layout.fillWidth: true
            text: control.displayText
            font: control.font
            horizontalAlignment: Text.AlignLeft
        }
        Text {
            text: "▾"
            color: text.color
        }
    }
    popup: T.Popup {
        width: control.width
        implicitHeight: listview.contentHeight
        transformOrigin: Item.Top
        topMargin: 12
        bottomMargin: 12
        enter: Transition {
            // grow_fade_in
            NumberAnimation { property: "scale"; from: 0.9; to: 1.0; easing.type: Easing.OutQuint; duration: 220 }
            NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; easing.type: Easing.OutCubic; duration: 150 }
        }
        exit: Transition {
            // shrink_fade_out
            NumberAnimation { property: "scale"; from: 1.0; to: 0.9; easing.type: Easing.OutQuint; duration: 220 }
            NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; easing.type: Easing.OutCubic; duration: 150 }
        }
        contentItem: ListView {
            id: listview
            clip: true
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            T.ScrollIndicator.vertical: ScrollIndicator { }
        }
        background: Rectangle {
            color: Globals.window.color.dark
        }
    }

}
