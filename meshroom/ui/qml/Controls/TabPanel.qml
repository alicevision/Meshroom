import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

Page {
    id: root

    property alias headerBar: headerLayout.data
    property alias footerContent: footerLayout.data

    property var tabs: []
    property int currentTab: 0

    clip: true

    QtObject {
        id: m
        property int hPadding: 6
        property int vPadding: 4
        property int topPadding: 4
        readonly property color paneBackgroundColor: Qt.darker(root.palette.window, 1.15)
    }

    padding: 1


    header: Pane {
        id: headerPane
        topPadding: m.topPadding; bottomPadding: m.vPadding
        leftPadding: m.hPadding; rightPadding: m.hPadding
        background: Rectangle { color: m.paneBackgroundColor }

        RowLayout {
            width: parent.width

            TabBar {
                id: mainTabBar
                Layout.fillWidth: true
                onCurrentIndexChanged: root.currentTab = currentIndex
                anchors.bottom: parent.bottom
                anchors.bottomMargin: -4

                Repeater {
                    model: root.tabs

                    TabButton {
                        text: modelData
                        padding: 4
                        width: 150
                        background: Rectangle {
                            color: index === mainTabBar.currentIndex ? root.palette.window : Qt.darker(root.palette.window, 1.30)
                        }

                        Rectangle {
                            property bool commonBorder : false

                            property int lBorderwidth : index === mainTabBar.currentIndex ? 2 : 1
                            property int rBorderwidth : index === mainTabBar.currentIndex ? 2 : 1
                            property int tBorderwidth : index === mainTabBar.currentIndex ? 2 : 1
                            property int bBorderwidth : 0

                            property int commonBorderWidth : 1

                            z : -1

                            color: Qt.darker(root.palette.window, 1.50)

                            anchors {
                                left: parent.left
                                right: parent.right
                                top: parent.top
                                bottom: parent.bottom

                                topMargin    : commonBorder ? -commonBorderWidth : -tBorderwidth
                                bottomMargin : commonBorder ? -commonBorderWidth : -bBorderwidth
                                leftMargin   : commonBorder ? -commonBorderWidth : -lBorderwidth
                                rightMargin  : commonBorder ? -commonBorderWidth : -rBorderwidth
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
        topPadding: m.vPadding; bottomPadding: m.vPadding
        leftPadding: m.hPadding; rightPadding: m.hPadding
        visible: footerLayout.children.length > 0
        background: Rectangle { color: m.paneBackgroundColor }

        RowLayout {
            id: footerLayout
            width: parent.width
        }
    }
}
