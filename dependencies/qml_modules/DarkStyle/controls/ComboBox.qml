import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
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
            Image {
                source: "qrc:///images/arrow_right_outline.svg"
                sourceSize: Qt.size(20, 20)
                transform: Rotation { origin.x: 10; origin.y: 10; angle: 90 }
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.bottomMargin: 5
                anchors.rightMargin: 5
            }
        }
        label: Text {
            anchors.fill: parent
            anchors.margins: 3
            text: control.currentText
        }
    }

}
