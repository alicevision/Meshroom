import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Utils 1.0

import MaterialIcons

/**
* ComboBox with filtering capabilities and support for custom values (i.e: outside the source model).
*/

ComboBox {
    id: root

    // Model to populate the combobox.
    required property var sourceModel
    // Input value to use as the current combobox value.
    property var inputValue
    // The text to filter the combobox model when the choices are displayed.
    property alias filterText: filterTextArea.text
    // Whether the current input value is within the source model.
    readonly property bool validValue: sourceModel.includes(inputValue)

    signal editingFinished(var value)

    function clearFilter() {
        filterText = "";
    }

    // Re-computing current index when source values are set.
    Component.onCompleted: _updateCurrentIndex()
    onInputValueChanged: _updateCurrentIndex()
    onModelChanged: _updateCurrentIndex()

    function _updateCurrentIndex() {
        currentIndex = find(inputValue);
    }

    displayText: inputValue

    model: {
        return sourceModel.filter(item => {
            return item.toString().toLowerCase().includes(filterText.toLowerCase());
        });
    }

    popup.onClosed: clearFilter()

    // Allows typing into the filter text area while the combobox has focus.
    Keys.forwardTo: [filterTextArea]

    onActivated: index => {
        const isValidEntry = model.length > 0;
        if (!isValidEntry) {
            return;
        }
        editingFinished(model[index]);
    }

    StateGroup {
        id: filterState
        // Override properties depending on filter text status.
        states: [
            State {
                name: "Invalid"
                when: root.delegateModel.count === 0
                PropertyChanges {
                    target: filterTextArea
                    color: Colors.orange
                }
            }
        ]
    }

    popup.contentItem: ColumnLayout {
        width: parent.width
        Layout.maximumHeight: root.Window.height
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            spacing: 2

            TextField {
                id: filterTextArea
                placeholderText: "Type to filter..."
                Layout.fillWidth: true
                leftPadding: 18
                MouseArea {
                    // Prevent textfield from stealing combobox's active focus, without disabling it.
                    anchors.fill: parent
                }
                background: Item {
                    MaterialLabel {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 2
                        text: MaterialIcons.search
                    }
                }
            }

            MaterialToolButton {
                enabled: root.filterText !== ""
                text: MaterialIcons.add_task
                ToolTip.text: "Force custom value"
                onClicked: {
                    editingFinished(root.filterText);
                    root.popup.close();
                }
            }
        }

        Rectangle {
            height: 1
            Layout.fillWidth: true
            color: Colors.sysPalette.mid
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            ListView {
                implicitHeight: contentHeight
                clip: true

                model: root.delegateModel
                highlightRangeMode: ListView.ApplyRange
                currentIndex: root.highlightedIndex
                ScrollBar.vertical: ScrollBar {}
            }
        }
    }
}
