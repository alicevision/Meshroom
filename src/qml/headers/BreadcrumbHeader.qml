import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../styles"

Item {
    id: root
    property variant model: null

    implicitHeight: 60

    function selectCrumb(index) {
        crumbChanged(index);
        if(index < 0 || index >= root.model.count)
            return;
        breadcrumbList.currentIndex = index;
    }

    signal crumbChanged(int index)
    signal actionCancelled()

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        spacing: 20
        ListView {
            id: breadcrumbList
            Layout.fillWidth: true
            Layout.fillHeight: true
            interactive: false
            spacing: 20
            model: root.model
            orientation: ListView.Horizontal
            delegate: Item {
                anchors.verticalCenter: parent.verticalCenter
                height: parent.height
                width: childrenRect.width
                property variant crumbColor: (index <= breadcrumbList.currentIndex) ? "white" : "#444"
                RowLayout {
                    Layout.fillWidth: false
                    Layout.preferredWidth: childrenRect.width
                    anchors.verticalCenter: parent.verticalCenter
                    Rectangle {
                        Layout.preferredWidth: 6
                        Layout.preferredHeight: 6
                        radius: 6
                        color: crumbColor
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        color: crumbColor
                        elide: Text.ElideRight
                        wrapMode: Text.WrapAnywhere
                        text: model.name
                        maximumLineCount: 1
                        font.pointSize: 12
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: selectCrumb(index)
                    enabled: (index <= breadcrumbList.currentIndex)
                }
            }
        }
        RowLayout {
            Layout.fillWidth: false
            Layout.preferredWidth: childrenRect.width
            spacing: 10
            ToolButton {
                style: DefaultStyle.smallToolButton
                iconSource: 'qrc:/images/arrow_right_outline.svg'
                rotation: 180
                visible: (breadcrumbList.currentIndex > 0)
                onClicked: selectCrumb(breadcrumbList.currentIndex-1)
            }
            ToolButton {
                style: DefaultStyle.smallToolButton
                iconSource: 'qrc:/images/arrow_right_outline.svg'
                onClicked: selectCrumb(breadcrumbList.currentIndex+1)
            }
            ToolButton {
                style: DefaultStyle.smallToolButton
                iconSource: 'qrc:/images/close.svg'
                onClicked: actionCancelled()
            }
        }
    }
}
