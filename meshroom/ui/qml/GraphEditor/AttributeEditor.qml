import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2
import MaterialIcons 2.2
import Utils 1.0

/**
 * A component to display and edit the attributes of a Node.
 */

ListView {
    id: root
    property variant attributes: null
    property bool readOnly: false
    property int labelWidth: 180

    signal upgradeRequest()
    signal attributeDoubleClicked(var attribute)

    implicitHeight: contentHeight

    clip: true
    spacing: 2
    ScrollBar.vertical: ScrollBar { id: scrollBar }

    model: SortFilterDelegateModel {

        model: attributes
        filterRole: GraphEditorSettings.showAdvancedAttributes ? "" : "advanced"
        filterValue: false

        function modelData(item, roleName) {
            return item.model.object.desc[roleName]
        }

        Component {
            id: delegateComponent
            AttributeItemDelegate {
                width: ListView.view.width - scrollBar.width
                readOnly: root.readOnly
                labelWidth: root.labelWidth
                attribute: object
                onDoubleClicked: root.attributeDoubleClicked(attr)
            }
        }
    }

    // Helper MouseArea to lose edit/activeFocus
    // when clicking on the background
    MouseArea {
        anchors.fill: parent
        onClicked: root.forceActiveFocus()
        z: -1
    }
}

