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


    QtObject {
        id: m
        readonly property int delegateModelCount: root.delegateModel.count

        // Ensure the highlighted index is always within the range of delegates whenever the
        // combobox model changes, for combobox validation to always considers a valid item.
        onDelegateModelCountChanged: {
            if(delegateModelCount > 0 && root.highlightedIndex >= delegateModelCount) {
                while(root.highlightedIndex > 0 && root.highlightedIndex >= delegateModelCount) {
                    // highlightIndex is read-only, this method has to be used to change it programmatically.
                    root.decrementCurrentIndex();
                }
            }
        }
    }

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

    popup.onOpened: {
        filterTextArea.forceActiveFocus();
    }

    popup.onClosed: clearFilter()

    onActivated: (index) => {
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
                when: m.delegateModelCount === 0
                PropertyChanges {
                    target: filterTextArea
                    color: Colors.orange
                    // Prevent ComboBox validation when there are no entries in the model.
                    Keys.forwardTo: []
                }
            }
        ]
    }

    popup.contentItem: ColumnLayout {
        width: parent.width
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            spacing: 2

            TextField {
                id: filterTextArea
                placeholderText: "Type to filter..."
                Layout.fillWidth: true
                leftPadding: 18
                Keys.forwardTo: [root]

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
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

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
