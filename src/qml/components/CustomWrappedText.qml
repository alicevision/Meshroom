import QtQuick 2.5
import QtQuick.Controls 1.4

Item {
    id: root
    property string text: ""
    property int textSize: _style.text.size.normal
    property color color: enabled ? _style.text.color.normal : _style.text.color.disabled
    implicitHeight: childrenRect.height
    Text {
        width: parent.width
        font.pointSize: root.textSize>0 ? root.textSize : 10
        text: root.text
        color: root.color
        elide: Text.ElideRight
        wrapMode: Text.WrapAnywhere
        maximumLineCount: 1
        verticalAlignment: Text.AlignVCenter
    }
}
