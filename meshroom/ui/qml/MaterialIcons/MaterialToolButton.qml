import QtQuick 2.9
import QtQuick.Controls 2.3


/**
 * MaterialToolButton is a standard ToolButton using MaterialIcons font.
 * It also shows up its tooltip when hovered.
 */
ToolButton {
    font.family: MaterialIcons.fontFamily
    padding: 4
    font.pointSize: 13
    ToolTip.visible: ToolTip.text && hovered
    ToolTip.delay: 100
}
