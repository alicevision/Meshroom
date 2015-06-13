pragma Singleton
import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3


Item {

    // color: "#468bb7"
    // color: "#5BB1F7"

    readonly property int fontPointSize: 16

    readonly property Component application: ApplicationWindowStyle {
        background: Rectangle { color: "black" }
    }

    readonly property Component applicationGL: ApplicationWindowStyle {
        background: Item {} // hide default application background
    }

    readonly property Component applicationDebug: ApplicationWindowStyle {
        background: Rectangle { color: "#999" }
    }

    readonly property Component progressBar: ProgressBarStyle {
        background: Rectangle {
            color: "#222"
            implicitHeight: 24
            implicitWidth: 200
        }
        progress: Rectangle {
            color: control.enabled ? "#5BB1F7" : "#D82626"
            Text {
                property double value: Math.round((control.value - control.minimumValue)*100 / (control.maximumValue - control.minimumValue))
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                text: value + '%'
                color: "black"
                elide: Text.ElideRight
                wrapMode: Text.WrapAnywhere
                maximumLineCount: 1
                font.pointSize: 10
                visible: (value > 10)
            }
        }
    }

    readonly property Component slider: SliderStyle {
        handle: Rectangle {
            width: 20
            height: 20
            radius: height
            antialiasing: true
            color: "#5BB1F7"
        }
        groove: Item {
            implicitHeight: 10
            implicitWidth: 200
            Rectangle {
                height: 5
                width: parent.width
                anchors.verticalCenter: parent.verticalCenter
                color: "#444"
                opacity: 0.8
                Rectangle {
                    antialiasing: true
                    color: "#5BB1F7"
                    height: parent.height
                    width: parent.width * (control.value - control.minimumValue) / (control.maximumValue - control.minimumValue)
                }
                Text {
                    anchors.top: parent.bottom
                    anchors.right: parent.right
                    text: control.value
                    color: "white"
                    elide: Text.ElideRight
                    wrapMode: Text.WrapAnywhere
                    maximumLineCount: 1
                    font.pointSize: 12
                }
            }
        }
    }

    readonly property Component largeToolButton: ButtonStyle {
        panel: Item {
            implicitHeight: childrenRect.height
            implicitWidth: childrenRect.width
            Image {
                // width: 48
                // height: 48
                sourceSize.width: 48
                sourceSize.height: 48
                source: control.iconSource
            }
        }
    }

    readonly property Component smallToolButton: ButtonStyle {
        panel: Item {
            implicitHeight: childrenRect.height
            implicitWidth: childrenRect.width
            Image {
                // width: 24
                // height: 24
                sourceSize.width: 24
                sourceSize.height: 24
                source: control.iconSource
            }
        }
    }

    readonly property Component labeledToolButton: ButtonStyle {
        panel: Item {
            implicitHeight: childrenRect.height
            implicitWidth: childrenRect.width
            Item {
                width: childrenRect.width
                height: 48
                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                        text: control.tooltip
                        horizontalAlignment: Text.AlignHRight
                        color: "#444"
                        font.pointSize: 10
                    }
                    Text {
                        text: control.text ? control.text : "-"
                        color: "white"
                        font.pointSize: 12
                        elide: Text.ElideRight
                        wrapMode: Text.WrapAnywhere
                        maximumLineCount: 1
                    }
                }
            }
        }
    }

    readonly property Component button: ButtonStyle {
        panel: Item {
            implicitWidth: childrenRect.width
            implicitHeight: 30
            Rectangle {
                width: childrenRect.width
                height: parent.height
                color: (control.hovered || control.checked) ? "#5BB1F7" : Qt.darker("#5BB1F7", 1.2)
                opacity: control.pressed ? 1.0 : 0.5
                border.width : 1
                border.color : "#5BB1F7"
                Text {
                    text: control.text
                    anchors.verticalCenter: parent.verticalCenter
                    color: control.enabled ? "white" : "#444"
                    font.pointSize: 12
                    renderType: Text.NativeRendering
                }
            }
        }
    }

    readonly property Component breadcrumbButton: ButtonStyle {
        panel: Item {
            implicitWidth: childrenRect.width
            implicitHeight: 30
            Item {
                width: txt.implicitWidth
                height: parent.height
                Text {
                    id: txt
                    text: control.text
                    anchors.centerIn: parent
                    color: control.enabled ? (control.hovered ? "#5BB1F7" : "white") : "#444"
                    font.pointSize: 12
                    renderType: Text.NativeRendering
                }
            }
        }
    }

    readonly property Component textField: TextFieldStyle {
        textColor: control.enabled ? "white" : "#666"
        placeholderTextColor : "#444"
        font.pointSize: 14
        background: Rectangle {
            implicitHeight: 30
            implicitWidth: 200
            color: "#FF151515"
        }
    }

    readonly property Component textArea: TextAreaStyle {
        textColor: control.enabled ? "white" : "#666"
        selectionColor: "#5BB1F7"
        selectedTextColor: "white"
        backgroundColor: "#FF151515"
    }

    readonly property Component comboBox: ComboBoxStyle {
        font.pointSize: 14
        textColor: control.enabled ? "white" : "#666"
        background: Rectangle {
            implicitHeight: 30
            implicitWidth: 200
            color: "#FF151515"
        }
    }

}
