import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0
import MaterialIcons 2.2


/// Meshroom "About" window
Dialog {
    id: root

    x: parent.width / 2 - width / 2
    width: 600

    // Fade in transition
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0.0; to: 1.0 }
    }

    modal: true
    closePolicy: Dialog.CloseOnEscape | Dialog.CloseOnPressOutside
    padding: 30
    topPadding: 0  // header provides top padding

    header: Pane {
        background: Item {}
        MaterialToolButton {
            text: MaterialIcons.close
            anchors.right: parent.right
            onClicked: root.close()
        }
    }

    ColumnLayout {
        width: parent.width
        spacing: 6

        // Logo + Version info
        Column {
            Layout.fillWidth: true
            Image {
                anchors.horizontalCenter: parent.horizontalCenter
                source: "../img/meshroom-tagline-vertical.svg"
                sourceSize: Qt.size(222, 180)
            }
            TextArea {
                id: config
                width: parent.width
                readOnly: true
                horizontalAlignment: TextArea.AlignHCenter
                selectByKeyboard: true
                selectByMouse: true
                text: "Version " + Qt.application.version + "\n"
                      + MeshroomApp.systemInfo["platform"] + " \n"
                      + MeshroomApp.systemInfo["python"]
            }
        }

        SystemPalette { id: systemPalette }

        // Links
        Row {
            spacing: 4
            Layout.alignment: Qt.AlignHCenter
            MaterialToolButton {
                text: MaterialIcons._public
                font.pointSize: 21
                palette.buttonText: root.palette.link
                ToolTip.text: "AliceVision Website"
                onClicked: Qt.openUrlExternally("https://alicevision.github.io")
            }
            ToolButton {
                icon.source: "../img/GitHub-Mark-Light-32px.png"
                icon.width: 24
                icon.height: 24
                ToolTip.text: "Meshroom on Github"
                ToolTip.visible: hovered
                onClicked: Qt.openUrlExternally("https://github.com/alicevision/meshroom")
            }
            MaterialToolButton {
                text: MaterialIcons.bug_report
                font.pointSize: 21
                ToolTip.text: "Report a Bug (GitHub account required)"
                palette.buttonText: "#F44336"
                property string body: "**Configuration**\n" + config.text
                onClicked: Qt.openUrlExternally("https://github.com/alicevision/meshroom/issues/new?body="+body)
            }
            MaterialToolButton {
                text: MaterialIcons.forum
                font.pointSize: 21
                palette.buttonText: Qt.lighter(systemPalette.buttonText, 1.3)
                ToolTip.text: "Public Mailing-List (open discussions, use-cases, problems, best practices...)"
                onClicked: Qt.openUrlExternally("https://groups.google.com/forum/#!forum/alicevision")
            }
            MaterialToolButton {
                text: MaterialIcons.mail
                font.pointSize: 21
                palette.buttonText: Qt.lighter(systemPalette.buttonText, 1.3)
                ToolTip.text: "Private Contact (alicevision-team@googlegroups.com)"
                onClicked: Qt.openUrlExternally("mailto:alicevision-team@googlegroups.com")
            }
        }

        // Copyright
        RowLayout {
            spacing: 2
            Layout.alignment: Qt.AlignHCenter
            Label {
                font.family: MaterialIcons.fontFamily
                text: MaterialIcons.copyright
                font.pointSize: 10
            }
            Label {
                text: "2018 AliceVision contributors"
            }
        }

        // Spacer
        Rectangle {
            width: 50
            height: 1
            color: systemPalette.mid
            Layout.alignment: Qt.AlignHCenter
        }

        // OpenSource licenses
        Label {
             text: "Open Source Licenses"
             Layout.alignment: Qt.AlignHCenter
        }

        ListView {
            Layout.fillWidth: true
            implicitHeight: childrenRect.height
            spacing: 2
            interactive: false

            model: MeshroomApp.licensesModel

            // Exclusive ButtonGroup for licenses entries
            ButtonGroup { id: licensesGroup; exclusive: true }

            delegate: ColumnLayout {
                width: ListView.view.width
                Button {
                    id: sectionButton
                    flat: true
                    text: modelData.title
                    font.pointSize: 10
                    font.bold: true
                    checkable: true
                    ButtonGroup.group: licensesGroup
                    Layout.alignment: Qt.AlignHCenter
                }

                Loader {
                    Layout.fillWidth: true
                    active: sectionButton.checked
                    Layout.preferredHeight: active ? 210 : 0
                    visible: active

                    // Log display
                    sourceComponent: ScrollView {

                        Component.onCompleted: {
                            // try to load the local file
                            var url = Filepath.stringToUrl(modelData.localUrl)
                            // fallback to the online url if file is not found
                            if(!Filepath.exists(url))
                                url = modelData.onlineUrl
                            Request.get(url,
                                        function(xhr){
                                            if(xhr.readyState === XMLHttpRequest.DONE)
                                            {
                                                // status is OK
                                                if(xhr.status === 200)
                                                    textArea.text = MeshroomApp.markdownToHtml(xhr.responseText)
                                                else
                                                    textArea.text = "Could not load license file. Available online at <a href='" + url + "'>"+ url + "</a>."
                                            }
                                        })
                        }

                        background: Rectangle { color: palette.base }

                        TextArea {
                            id: textArea
                            readOnly: true
                            selectByMouse: true
                            selectByKeyboard: true
                            wrapMode: TextArea.WrapAnywhere
                            textFormat: TextEdit.RichText
                            onLinkActivated: Qt.openUrlExternally(link)
                        }
                    }
                }
            }
        }
    }
}
