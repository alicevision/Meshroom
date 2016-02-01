import QtQuick 2.5
import QtQuick.Controls 1.4
import ".."

Text {
    text: ""
    color: enabled ? Style.text.color.normal : Style.text.color.disabled
    font.pixelSize: Style.text.size.normal
    elide: Text.ElideRight
    wrapMode: Text.WrapAnywhere
    maximumLineCount: 1
    verticalAlignment: Text.AlignVCenter
}
