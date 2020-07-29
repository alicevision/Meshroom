import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3


/**
 * MaterialToolButton is a standard ToolButton using MaterialIcons font.
 * It also shows up its tooltip when hovered.
 */
ToolButton {
    id: control
    property alias iconText: icon.text
    property alias iconSize: icon.font.pointSize
    property alias label: labelItem.text
    padding: 0
    ToolTip.visible: ToolTip.text && hovered
    ToolTip.delay: 100
    width: childrenRect.width
    height: childrenRect.height
    contentItem: RowLayout {
        Layout.margins: 0
        Label {
            id: icon
            font.family: MaterialIcons.fontFamily
            font.pointSize: 13
            padding: 0
            text: ""
            color: (checked ? palette.highlight : palette.text)
        }
        Label {
            id: labelItem
            text: ""
            padding: 0
            color: (checked ? palette.highlight : palette.text)
        }
    }
    background: Rectangle {
        color: {
            if(pressed || checked || hovered)
            {
                if(pressed || checked)
                    return Qt.darker(parent.palette.base, 1.3)
                if(hovered)
                    return Qt.darker(parent.palette.base, 0.6)
            }
            return "transparent";
        }

        border.color: checked ? Qt.darker(parent.palette.base, 1.4) : "transparent"
    }
}
