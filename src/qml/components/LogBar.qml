import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2

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
        if(!root.model)
            return;
        titleText.text = (root.model.count > 0) ? root.model.data(root.model.index(root.model.count-1,0), 258) : "";
        titleText.color = (root.model.count > 0) ? getLogColor(root.model.data(root.model.index(root.model.count-1,0), 257)) : "white";
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

    width: parent.width
    height: expanded ? 5 * root.itemHeight : root.itemHeight
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
                color: _style.window.color.xdarker
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
            CustomScrollView {
                anchors.fill: parent
                verticalScrollBarPolicy: Qt.ScrollBarAlwaysOn
                ListView {
                    id: logView
                    model: root.model
                    delegate: Item {
                        width: parent.width
                        height: root.itemHeight
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 4
                            anchors.rightMargin: 4
                            CustomText {
                                text: "["+index+"]"
                                textSize: _style.text.size.small
                                color: _style.text.color.darker
                            }
                            CustomWrappedText {
                                Layout.fillWidth: true
                                text: message
                                textSize: _style.text.size.small
                                color: getLogColor(type)
                            }
                        }
                    }
                    spacing: 0
                    interactive: false
                    onCountChanged: {
                        if(!root.expanded)
                            showTitleText();
                        logView.positionViewAtIndex(logView.count - 1, ListView.Contain);
                    }
                }
            }
        }
    }
}
