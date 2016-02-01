import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import ".."
import "."

Item {

    id: root

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        RowLayout {
            spacing: 0
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 10
                color: Style.window.color.xlight
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 10
                color: Style.window.color.light
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 10
                color: Style.window.color.normal
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 10
                color: Style.window.color.dark
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 10
                color: Style.window.color.xdark
            }
        }
        TabView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Tab {
                title: "Text"
                TabView {
                    Tab {
                        title: "size"
                        Column {
                            anchors.fill: parent
                            anchors.margins: 20
                            Text {
                                font.pixelSize: Style.text.size.xsmall
                                text: "size: xsmall"
                            }
                            Text {
                                font.pixelSize: Style.text.size.small
                                text: "size: small"
                            }
                            Text {
                                font.pixelSize: Style.text.size.normal
                                text: "size: normal"
                            }
                            Text {
                                font.pixelSize: Style.text.size.large
                                text: "size: large"
                            }
                            Text {
                                font.pixelSize: Style.text.size.xlarge
                                text: "size: xlarge"
                            }
                        }
                    }
                    Tab {
                        title: "color"
                        Column {
                            anchors.fill: parent
                            anchors.margins: 20
                            Text {
                                color: Style.text.color.xlight
                                text: "color: xlight"
                            }
                            Text {
                                color: Style.text.color.light
                                text: "color: light"
                            }
                            Text {
                                color: Style.text.color.normal
                                text: "color: normal"
                            }
                            Text {
                                color: Style.text.color.dark
                                text: "color: dark"
                            }
                            Text {
                                color: Style.text.color.xdark
                                text: "color: xdark"
                            }
                            Text {
                                color: Style.text.color.disabled
                                text: "color: disabled"
                            }
                            Text {
                                color: Style.text.color.selected
                                text: "color: selected"
                            }
                        }
                    }
                    Tab {
                        title: "log"
                        Column {
                            anchors.fill: parent
                            anchors.margins: 20
                            Text {
                                color: Style.text.color.debug
                                text: "log: debug"
                            }
                            Text {
                                color: Style.text.color.info
                                text: "log: info"
                            }
                            Text {
                                color: Style.text.color.warning
                                text: "log: warning"
                            }
                            Text {
                                color: Style.text.color.critical
                                text: "log: critical"
                            }
                            Text {
                                color: Style.text.color.fatal
                                text: "log: fatal"
                            }
                        }
                    }
                }
            }
            Tab {
                title: "Controls"
                TabView {
                    anchors.fill: parent
                    Tab {
                        title: "Button"
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            ToolButton {}
                            ToolButton {}
                            ToolButton {}
                        }
                    }
                    Tab {
                        title: "Slider"
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            Slider { Layout.fillWidth: true }
                            Slider { Layout.fillWidth: true }
                            Slider { Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                        }
                    }
                    Tab {
                        title: "ComboBox"
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            ComboBox { Layout.fillWidth: true }
                            ComboBox { Layout.fillWidth: true }
                            ComboBox { Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                        }
                    }
                    Tab {
                        title: "TextField"
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            TextField { Layout.fillWidth: true }
                            TextField { Layout.fillWidth: true }
                            TextField { Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                        }
                    }
                }
            }
        }

    }
}
