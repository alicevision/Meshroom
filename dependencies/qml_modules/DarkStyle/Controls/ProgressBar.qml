import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import ".."
import "."

ProgressBar {

    id: root
    property variant color: Style.window.color.selected

    style: ProgressBarStyle {
        background: Rectangle {
            color: Style.window.color.xdark
            implicitWidth: 100
            implicitHeight: 18
        }
        progress: Rectangle {
            color: root.color
        }
    }

}
