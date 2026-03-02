import QtQuick
import Meshroom.Helpers

/*
A SelectionBox that can be used to select delegates in a model instantiator (Repeater, ListView...).
Interesection test is done in the coordinate system of the container Item, using delegate's bounding boxes.
The list of selected indices is emitted when the selection ends.
*/

SelectionBox {
    id: root

    // The Item instantiating the delegates.
    property Item modelInstantiator
    // The Item containing the delegates (used for coordinate mapping).
    property Item container
    // Emitted when the selection has ended, with the list of selected indices and modifiers.
    signal delegateSelectionEnded(list<int> indices, int modifiers)

    onSelectionEnded: function(selectionRect, modifiers) {
        let selectedIndices = [];
        const mappedSelectionRect = mapToItem(container, selectionRect)
        for (var i = 0; i < modelInstantiator.count; ++i) {
            const delegate = modelInstantiator.getItemAt(i)
            if (!delegate)
                continue
            // For backdrop nodes, only select when the selection rect intersects the titlebar.
            const delegateRect = Qt.rect(delegate.x, delegate.y, delegate.width, delegate.isBackdropNode ? delegate.headerHeight : delegate.height)
            if (Geom2D.rectRectIntersect(mappedSelectionRect, delegateRect)) {
                selectedIndices.push(i)

                if (delegate.isBackdropNode) {
                    let children = delegate.getChildrenIndices(true)
                    for (var child = 0; child < children.length; ++child) {
                        if (selectedIndices.indexOf(children[child]) === -1) {
                            selectedIndices.push(children[child])
                        }
                    }
                }
            }
        }
        delegateSelectionEnded(selectedIndices, modifiers)
    }
}
