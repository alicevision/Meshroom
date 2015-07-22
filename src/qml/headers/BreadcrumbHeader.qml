import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../components"

Rectangle {

    id: root
    property variant model: null
    property string title: ""

    implicitHeight: 60
    color: _style.window.color.darker

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
        CustomText {
            text: root.title
            textSize: _style.text.size.large
            color: _style.text.color.disabled
        }
        ListView {
            id: breadcrumbList
            Layout.fillWidth: true
            Layout.fillHeight: true
            interactive: false
            spacing: 10
            model: root.model
            orientation: ListView.Horizontal
            delegate: Item {
                height: ListView.view.height
                width: childrenRect.width
                property variant crumbColor: (index <= breadcrumbList.currentIndex) ? "white" : "#444"
                RowLayout {
                    height: parent.height
                    Layout.fillWidth: false
                    Layout.preferredWidth: childrenRect.width
                    spacing: 10
                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: parent.height / 3
                        color: _style.window.color.lighter
                    }
                    CustomText {
                        text: model.name
                        color: crumbColor
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
            spacing: 2
            CustomToolButton {
                iconSource: 'qrc:///images/arrow_right_outline.svg'
                rotation: 180
                visible: (breadcrumbList.currentIndex > 0)
                onClicked: selectCrumb(breadcrumbList.currentIndex-1)
            }
            CustomToolButton {
                iconSource: 'qrc:///images/arrow_right_outline.svg'
                onClicked: selectCrumb(breadcrumbList.currentIndex+1)
            }
            CustomToolButton {
                iconSource: 'qrc:///images/close.svg'
                onClicked: actionCancelled()
            }
        }
    }
}
