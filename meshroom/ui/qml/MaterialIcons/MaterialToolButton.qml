import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Utils 1.0

/**
 * MaterialToolButton is a standard ToolButton using MaterialIcons font.
 * It also shows up its tooltip when hovered.
 */

ToolButton {
    id: control
    font.family: MaterialIcons.fontFamily
    padding: UISettings.dp(4)
    font.pointSize: UISettings.mediumFont
    implicitWidth: UISettings.toolButtonSize
    implicitHeight: UISettings.toolButtonSize
    ToolTip.visible: ToolTip.text && hovered
    ToolTip.delay: 100
    Component.onCompleted:  {
        contentItem.color = Qt.binding(function() { return checked ? palette.highlight : palette.text })
    }
    background: Rectangle {
        color: {
            if (enabled && (pressed || checked || hovered)) {
                if (pressed || checked)
                    return Qt.darker(parent.palette.base, 1.3)
                if (hovered)
                    return Qt.darker(parent.palette.base, 0.6)
            }
            return "transparent"
        }

        border.color: checked ? Qt.darker(parent.palette.base, 1.4) : "transparent"
    }
}
