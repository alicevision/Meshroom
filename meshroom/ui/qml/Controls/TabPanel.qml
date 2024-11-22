import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: root

    property alias headerBar: headerLayout.data
    property alias footerContent: footerLayout.data

    property var tabs: []
    property int currentTab: 0

    clip: true

    QtObject {
        id: m
        readonly property color paneBackgroundColor: Qt.darker(root.palette.window, 1.15)
    }
    padding: 0

    header: Pane {
        id: headerPane
        padding: 0
        background: Rectangle { color: m.paneBackgroundColor }

        RowLayout {
            width: parent.width
            spacing: 0

            TabBar {
                id: mainTabBar
                padding: 4
                Layout.fillWidth: true
                onCurrentIndexChanged: root.currentTab = currentIndex

                Repeater {
                    model: root.tabs

                    TabButton {
                        text: modelData
                        y: mainTabBar.padding
                        padding: 4
                        width: text.length * font.pointSize
                        background: Rectangle {
                            color: index === mainTabBar.currentIndex ? root.palette.window : Qt.darker(root.palette.window, 1.30)
                        }

                        Rectangle {
                            property bool commonBorder: false

                            property int lBorderwidth: index === mainTabBar.currentIndex ? 2 : 1
                            property int rBorderwidth: index === mainTabBar.currentIndex ? 2 : 1
                            property int tBorderwidth: index === mainTabBar.currentIndex ? 2 : 1
                            property int bBorderwidth: 0

                            property int commonBorderWidth: 1

                            z: -1

                            color: Qt.darker(root.palette.window, 1.50)

                            anchors {
                                left: parent.left
                                right: parent.right
                                top: parent.top
                                bottom: parent.bottom

                                topMargin: commonBorder ? -commonBorderWidth : -tBorderwidth
                                bottomMargin: commonBorder ? -commonBorderWidth : -bBorderwidth
                                leftMargin: commonBorder ? -commonBorderWidth : -lBorderwidth
                                rightMargin: commonBorder ? -commonBorderWidth : -rBorderwidth
                            }
                        }
                    }
                }
            }

            Row { id: headerLayout }
        }
    }

    footer: Pane {
        id: footerPane
        visible: footerLayout.children.length > 0
        background: Rectangle { color: m.paneBackgroundColor }

        RowLayout {
            id: footerLayout
            width: parent.width
        }
    }
}
