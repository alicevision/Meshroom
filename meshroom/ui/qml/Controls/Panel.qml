import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3


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
        background: Rectangle { color: m.paneBackgroundColor }

        RowLayout {
            width: parent.width

            // Icon
            Item {
                id: iconPlaceHolder
                width: childrenRect.width
                height: childrenRect.height
                Layout.alignment: Qt.AlignVCenter
                visible: icon != ""
            }

            // Title
            Label {
                text: root.title
                Layout.fillWidth: true
                elide: Text.ElideRight
                topPadding: m.vPadding
                bottomPadding: m.vPadding
            }
            //
            Row { id: headerLayout }
        }
    }

    footer: Pane {
        id: footerPane
        topPadding: m.vPadding; bottomPadding: m.vPadding
        leftPadding: m.hPadding; rightPadding: m.hPadding
        visible: footerLayout.children.length > 0
        background: Rectangle { color: m.paneBackgroundColor }

        // Content place holder
        RowLayout {
            id: footerLayout
            width: parent.width
        }
    }
}
