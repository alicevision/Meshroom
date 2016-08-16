import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Templates 2.0 as T

import "."

T.ComboBox {

    id: control
    implicitWidth: 200
    implicitHeight: 30
    spacing: 10
    padding: 2

    background: Rectangle {
        color: Globals.window.color.dark
    }
    delegate: MenuItem {
        width: control.width
        text: modelData
        highlighted: control.highlightedIndex === index
    }
    contentItem: Text {
        leftPadding: control.leftPadding
        rightPadding: control.rightPadding
        text: control.displayText
        font: control.font
        color: control.enabled ? Globals.text.color.normal : Globals.text.color.disabled
        horizontalAlignment: Text.AlignLeft
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
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
