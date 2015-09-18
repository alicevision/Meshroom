import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

ComboBox {
    id: root
    style: ComboBoxStyle {
        font.pixelSize: _style.text.size.normal
        textColor: control.enabled ? _style.text.color.normal : _style.text.color.disabled
        background: Rectangle {
            implicitHeight: 30
            implicitWidth: 300
            color: _style.window.color.xdarker
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
        label: CustomWrappedText {
            anchors.fill: parent
            anchors.margins: 3
            text: control.currentText
        }
    }
}
