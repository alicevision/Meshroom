import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * Panel is a container control with preconfigured header/footer.
 *
 * The header displays an optional icon and the title of the Panel,
 * and provides a placeholder (headerBar) at the top right corner, useful to create a contextual toolbar.
 *
 *
 * The footer is empty (and not visible) by default. It does not provided any layout.
 */

Page {
    id: root

    property alias headerBar: headerLayout.data
    property alias footerContent: footerLayout.data
    property alias icon: iconPlaceHolder.data
    property alias loading: loadingIndicator.running
    property alias loadingText: loadingLabel.text

    clip: true

    QtObject {
        id: m
        property int hPadding: 6
        property int vPadding: 4
        readonly property color paneBackgroundColor: Qt.darker(root.palette.window, 1.15)
    }

    padding: 1

    header: Pane {
        id: headerPane
        topPadding: m.vPadding; bottomPadding: m.vPadding
        leftPadding: m.hPadding; rightPadding: m.hPadding
        background: Item {
            Rectangle {
                anchors.fill: parent
                color: m.paneBackgroundColor
            }
            MouseArea {
                anchors.fill: parent
                onPressed: {
                    headerLayout.forceActiveFocus()
                }
            }
        }

        RowLayout {
            width: parent.width

            // Icon
            Item {
                id: iconPlaceHolder
                width: childrenRect.width
                height: childrenRect.height
                Layout.alignment: Qt.AlignVCenter
                visible: icon !== ""
            }

            // Title
            Label {
                text: root.title
                elide: Text.ElideRight
                topPadding: m.vPadding
                bottomPadding: m.vPadding
            }
            Item {
                width: 10
            }
            // Feature loading status
            BusyIndicator {
                id: loadingIndicator
                padding: 0
                implicitWidth: 12
                implicitHeight: 12
                running: false
            }
            Label {
                id: loadingLabel
                text: ""
                font.italic: true
            }
            Item {
                Layout.fillWidth: true
            }

            // Header menu
            Row { id: headerLayout }
        }
    }

    footer: Pane {
        id: footerPane
        topPadding: m.vPadding; bottomPadding: m.vPadding
        leftPadding: m.hPadding; rightPadding: m.hPadding
        visible: footerLayout.children.length > 0
        background: Item {
            Rectangle {
                anchors.fill: parent
                color: m.paneBackgroundColor
            }
            MouseArea {
                anchors.fill: parent
                onPressed: {
                    footerLayout.forceActiveFocus()
                }
            }
        }

        // Content place holder
        RowLayout {
            id: footerLayout
            width: parent.width
        }
    }
}
