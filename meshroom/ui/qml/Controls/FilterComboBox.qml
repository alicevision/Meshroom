import QtQuick 2.15
import QtQuick.Controls 2.15
import Utils 1.0

/**
* ComboBox with filter text area
*
* @param inputModel - model to filter
* @param editingFinished - signal emitted when editing is finished
* @alias filterText - text to filter the model
*/

ComboBox {
    id: combo

    property var inputModel
    signal editingFinished(var value)

    property alias filterText: filterTextArea

    enabled: root.editable
    model: {
        var filteredData = inputModel.filter(condition => {
                                            if (filterTextArea.text.length > 0) return condition.toString().includes(filterTextArea.text)
                                            return true
                                        })
        if (filteredData.length > 0) {
            filterTextArea.background.color = Qt.lighter(palette.base, 2)

            // order filtered data by relevance (results that start with the filter text come first)
            filteredData.sort((a, b) => {
                const nameA = a.toString().toLowerCase();
                const nameB = b.toString().toLowerCase();
                const filterText = filterTextArea.text.toLowerCase()
                if (nameA.startsWith(filterText) && !nameB.startsWith(filterText))
                    return -1
                if (!nameA.startsWith(filterText) && nameB.startsWith(filterText))
                    return 1
                return 0
            })
        } else {
            filterTextArea.background.color = Colors.red
        }

        if (filteredData.length == 0 || filterTextArea.length == 0) {
            filteredData = inputModel
        } 

        return filteredData
    }

    popup: Popup {
        width: combo.width
        implicitHeight: contentItem.implicitHeight

        onAboutToShow: {
            filterTextArea.forceActiveFocus()
        }

        contentItem: Item {
            anchors.fill: parent
            TextArea {
                id: filterTextArea
                leftPadding: 12
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top

                selectByMouse: true
                hoverEnabled: true
                wrapMode: TextEdit.WrapAnywhere
                placeholderText: "Filter"
                background: Rectangle {}

                onEditingFinished: {
                    combo.popup.close()
                    combo.editingFinished(currentText)
                }

                Keys.onReturnPressed: {
                    editingFinished()
                }
            }
        }

        ListView {
            clip: true
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: filterTextArea.bottom

            implicitHeight: contentHeight
            model: combo.popup.visible ? combo.delegateModel : null
            currentIndex: combo.highlightedIndex

            ScrollIndicator.vertical: ScrollIndicator {}
        }
    }

    delegate: ItemDelegate {
        width: combo.width
        height: combo.height

        contentItem: Text {
            text: modelData
            color: palette.text
        }

        highlighted: combo.highlightedIndex === index
    }
}
