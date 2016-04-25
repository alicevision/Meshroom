import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import ".."
import "."

ComboBox {

    id: root

    style: ComboBoxStyle {
        font.pixelSize: Style.text.size.normal
        textColor: control.enabled ? Style.text.color.normal : Style.text.color.disabled
        background: Rectangle {
            implicitHeight: 30
            implicitWidth: 300
            color: Style.window.color.xdark
        }
        label: Text {
            anchors.fill: parent
            anchors.margins: 3
            text: control.currentText
        }
        property Component __dropDownStyle: MenuStyle {
            frame: Rectangle {
                color: Style.window.color.xdark
            }
            itemDelegate {
                background: Rectangle {
                    color: Style.window.color.dark
                }
                label: Text {
                    text: styleData.text
                    font.pixelSize: Style.text.size.small
                    color: styleData.enabled ? (styleData.selected ? Style.text.color.selected : Style.text.color.normal) : Style.text.color.dark
                    height: 20
                }
                submenuIndicator: Image {
                    y: -12
                    sourceSize: Qt.size(100, 100)
                    width: 20
                    height: 20
                    source: "qrc:///images/arrow.svg"
                    smooth: true
                    opacity: styleData.enabled ? 1 : 0.5
                }
                shortcut: Text {
                    text: styleData.shortcut
                    font.pixelSize: Style.text.size.small
                    color: styleData.selected ? Style.text.color.selected : Style.text.color.normal
                }
                checkmarkIndicator: Rectangle {
                    width: 8
                    height: 8
                    radius: 8
                    color: styleData.checked ? Style.window.color.selected : Style.window.color.normal
                }
            }
            separator: Item {
                width: parent.width
                height: 10
                Rectangle {
                    anchors.centerIn: parent
                    implicitHeight: 1
                    implicitWidth: parent.width
                    color: Style.window.color.normal
                }
            }
        }
    }
}
