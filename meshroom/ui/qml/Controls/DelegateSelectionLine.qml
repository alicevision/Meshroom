import QtQuick
import Meshroom.Helpers

/*
A SelectionLine that can be used to select delegates in a model instantiator (Repeater, ListView...).
Interesection test is done in the coordinate system of the container Item, using delegate's bounding boxes.
The list of selected indices is emitted when the selection ends.
*/

SelectionLine {
    id: root

    // The Item instantiating the delegates.
    property Item modelInstantiator
    // The Item containing the delegates (used for coordinate mapping).
    property Item container
    // Emitted when the selection has ended, with the list of selected indices and modifiers.
    signal delegateSelectionEnded(list<int> indices, int modifiers)

    onSelectionEnded: function(selectionRect, modifiers) {
        let selectedIndices = [];
        const mappedSelectionRect = mapToItem(container, selectionRect);
        for (var i = 0; i < modelInstantiator.count; ++i) {
            const delegate = modelInstantiator.itemAt(i);
            if (delegate.intersects(mappedSelectionRect)) {
                selectedIndices.push(i);
            }
        }
        delegateSelectionEnded(selectedIndices, modifiers);
    }
}
