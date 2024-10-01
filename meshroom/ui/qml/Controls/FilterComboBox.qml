import QtQuick
import QtQuick.Controls

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
    property bool validValue: true

    enabled: root.editable
    model: {
        var filteredData = inputModel.filter(condition => {
                                            if (filterTextArea.text.length > 0) return condition.toString().toLowerCase().includes(filterTextArea.text.toLowerCase())
                                            return true
                                        })
        if (filteredData.length > 0) {
            filterTextArea.background.color = Qt.lighter(palette.base, 2)
            validValue = true

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
            validValue = false
        }

        if (filteredData.length == 0 || filterTextArea.length == 0) {
            filteredData = inputModel
        } 

        return filteredData
    }

    background: Rectangle {
        implicitHeight: root.implicitHeight
        color: {
            if (validValue) {
                return palette.mid
            } else {
                return Colors.red
            }
        }
        border.color: palette.base
    }

    popup: Popup {
        width: combo.width
        implicitHeight: contentItem.implicitHeight 

        onAboutToShow: {
            filterTextArea.forceActiveFocus()

            if (mapToGlobal(popup.x, popup.y).y + root.implicitHeight * (model.length + 1) > _window.contentItem.height) {
                y = -((combo.height * (combo.model.length + 1) > _window.contentItem.height) ? _window.contentItem.height*2/3 : combo.height * (combo.model.length + 1))
            } else {
                y = 0
            }
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
                    combo.editingFinished(displayText)
                }

                Keys.onEnterPressed: {
                    if (!validValue) {
                        displayText = filterTextArea.text
                    } else {
                        displayText = currentText
                    }
                    editingFinished()
                }

                Keys.onReturnPressed: {
                    if (!validValue) {
                        displayText = filterTextArea.text
                    } else {
                        displayText = currentText
                    }
                    editingFinished()
                }

                Keys.onUpPressed: {
                    // if the current index is 0, the user wants to go to the last item
                    if (combo.currentIndex == 0) {
                        combo.currentIndex = combo.model.length - 1
                    } else {
                        combo.currentIndex--
                    }
                }

                Keys.onDownPressed: {
                    // if the current index is the last one, the user wants to go to the first item
                    if (combo.currentIndex == combo.model.length - 1) {
                        combo.currentIndex = 0
                    } else {
                        combo.currentIndex++
                    }
                }
            }
        }

        ListView {
            id: listView
            clip: true
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: filterTextArea.bottom

            implicitHeight: (combo.height * (combo.model.length + 1) > _window.contentItem.height) ? _window.contentItem.height*2/3 : contentHeight
            model: combo.popup.visible ? combo.delegateModel : null

            ScrollBar.vertical: MScrollBar {}
        }
    }

    delegate: ItemDelegate {
        width: combo.width
        height: combo.height

        contentItem: Text {
            text: modelData
            color: palette.text
        }

        highlighted: validValue ? combo.currentIndex === index : false

        hoverEnabled: true
    }

    onHighlightedIndexChanged: {
        if (highlightedIndex >= 0) {
            combo.currentIndex = highlightedIndex
        }
    }

    onCurrentTextChanged: {
        displayText = currentText
    }
}
