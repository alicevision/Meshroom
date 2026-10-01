import QtQuick
import QtQuick.Controls

import MaterialIcons 2.2

/**
 * Flat icon button reflecting an on/off state (@p active), dimmed when off.
 * The state is not toggled internally: handle onClicked to update the source of @p active.
 */
MaterialToolButton {
    id: root

    property bool active: false
    property string activeIcon: ""
    property string inactiveIcon: activeIcon
    property string activeToolTip: ""
    property string inactiveToolTip: activeToolTip
    property real inactiveOpacity: 0.6

    text: active ? activeIcon : inactiveIcon
    font.pointSize: 10
    flat: true
    opacity: active ? 1.0 : inactiveOpacity
    ToolTip.text: active ? activeToolTip : inactiveToolTip
}
