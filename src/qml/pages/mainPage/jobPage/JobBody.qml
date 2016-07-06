import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import "jobBody"

Item {

    RowLayout {
        anchors.fill: parent
        spacing: -1
        TabView {
            id: tabview
            Layout.fillWidth: true
            Layout.fillHeight: true
            Tab {
                title: "images"
                JobImages {
                    anchors.fill: parent
                }
            }
            Tab {
                title: "parameters"
                JobSettings {
                    anchors.fill: parent
                }
            }
            Tab {
                title: "3D"
                Job3D {
                    anchors.fill: parent
                }
            }
            onCurrentIndexChanged: {
                jobPageTabChanged(currentIndex)
            }
        }
        Rectangle { // vertical tabs
            Layout.preferredWidth: 20
            Layout.fillHeight: true
            color: Style.window.color.dark
            ListView {
                anchors.fill: parent
                model: tabview.count
                spacing: 1
                interactive: false
                delegate: MouseArea {
                    id: mouseContainer
                    property bool tabEnabled: tabview.getTab(index).enabled
                    property bool tabSelected: tabview.currentIndex == index
                    width: parent.width
                    height: childrenRect.height
                    enabled: tabEnabled
                    cursorShape: tabEnabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    hoverEnabled: true
                    onClicked: tabview.currentIndex = index
                    Rectangle { // background
                        width: parent.width
                        height: title.width + 30
                        color: Style.window.color.xdark
                        opacity: tabSelected ? 1 : 0.6
                        Rectangle { // separator
                            width: parent.width
                            height: 1
                            color: Style.window.color.normal
                            y: parent.height
                        }
                    }
                    Text { // title txt
                        id: title
                        text: tabview.getTab(index).title
                        font.pixelSize: Style.text.size.xsmall
                        transform: Rotation { origin.x: 0; origin.y: 15; angle: 90}
                        color: tabSelected ? Style.text.color.selected : Style.text.color.normal
                    }
                    Rectangle { // selection indicator
                        width: 1
                        height: parent.height
                        color: {
                            if(tabSelected)
                                return Style.window.color.selected;
                            if(mouseContainer.containsMouse)
                                return Style.window.color.xlight;
                            return Style.window.color.xdark;
                        }
                    }
                }
            }
        }
    }

}
