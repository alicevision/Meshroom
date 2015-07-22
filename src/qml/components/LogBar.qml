import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1

import "../components"

Item {

    id: root
    property variant model: null // logs model
    property bool expanded: false
    property int itemHeight: 24

    function getLogColor(logType) {
        switch(logType) {
            case 0: return _style.log.color.debug;
            case 1: return _style.log.color.warning;
            case 2: return _style.log.color.critical;
            case 3: return _style.log.color.fatal;
            default: return _style.log.color.info;
        }
    }

    function showTitleText() {
        titleText.text = (root.model.length > 0) ? root.model[root.model.length-1].message : "";
        titleText.color = (root.model.length > 0) ? getLogColor(root.model[root.model.length-1].type) : "white";
        if(!root.expanded) titleText.opacity = 1;
        logTimer.restart();
    }
    function hideTitleText() {
        titleText.opacity = 0;
    }

    Timer {
        id: logTimer
        interval: 3000
        running: false
        repeat: false
        onTriggered: hideTitleText()
    }

    anchors.bottom: parent.bottom
    width: parent.width
    height: expanded ? Math.min(5, Math.max(model.length+1, 2)) * root.itemHeight : root.itemHeight
    Behavior on height { NumberAnimation {} }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: false
            Layout.preferredHeight: 25
            Rectangle {
                anchors.fill: parent
                color: _style.window.color.darker
            }
            RowLayout {
                anchors.fill: parent
                anchors.rightMargin: 10
                anchors.leftMargin: 10
                spacing: 2
                CustomText {
                    id: titleText
                    Layout.fillWidth: true
                    text: ""
                    textSize: _style.text.size.small
                    Behavior on opacity { NumberAnimation {} }
                }
                CustomText {
                    text: root.model.length
                    textSize: _style.text.size.xsmall
                }
                CustomToolButton {
                    tooltip: "console output"
                    iconSize: _style.icon.size.xsmall
                    iconSource: 'qrc:///images/monitor.svg'
                    onClicked: {
                        titleText.opacity = 0;
                        root.expanded = !root.expanded;
                    }
                }
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: _style.window.color.xdarker
            ScrollView {
                anchors.fill: parent
                verticalScrollBarPolicy: Qt.ScrollBarAlwaysOn
                ListView {
                    id: logView
                    model: root.model
                    delegate: Item {
                        width: parent.width
                        height: root.itemHeight
                        Item {
                            anchors.fill: parent
                            anchors.rightMargin: 10
                            anchors.leftMargin: 10
                            CustomText {
                                anchors.verticalCenter: parent.verticalCenter
                                text: modelData.message
                                textSize: _style.text.size.small
                                color: getLogColor(modelData.type)
                            }
                        }
                    }
                    spacing: 0
                    interactive: false
                    onModelChanged: {
                        showTitleText();
                        logView.positionViewAtIndex(logView.count - 1, ListView.Contain);
                    }
                }
            }
        }
    }
}
