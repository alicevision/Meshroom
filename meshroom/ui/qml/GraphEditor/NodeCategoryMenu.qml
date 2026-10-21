import QtQuick
import QtQuick.Controls

/**
 * Menu displaying a node category: its sub-categories as nested menus (recursively),
 * followed by the items of this category.
 */
Menu {
    id: root

    // Category tree: {"title": "Category", "menus": {"subCategoryKey": <tree>, ...}, "items": ["item1", "item2"]}
    property var tree
    // Component used to create the items, exposing the item name as "modelData"
    property Component itemDelegate

    title: tree ? tree.title : ""

    readonly property var subCategories: tree ? Object.values(tree.menus).sort((a, b) => a.title.localeCompare(b.title)) : []

    // Sub-categories first, inserted at the top of the menu in order
    Instantiator {
        model: root.subCategories
        // Recursion goes through Qt.createComponent as a QML component cannot instantiate itself inline
        delegate: Qt.createComponent("NodeCategoryMenu.qml")
        onObjectAdded: function(index, object) {
            object.itemDelegate = root.itemDelegate
            // Entries of nested sub-menus are created with the same delegate, set before the tree builds them
            object.delegate = root.delegate
            object.tree = root.subCategories[index]
            root.insertMenu(index, object)
        }
        onObjectRemoved: function(index, object) {
            root.removeMenu(object)
        }
    }

    // Then the items of this category
    Instantiator {
        model: root.tree ? root.tree.items : undefined
        delegate: root.itemDelegate
        onObjectAdded: function(index, object) {
            root.addItem(object)
        }
        onObjectRemoved: function(index, object) {
            root.removeItem(object)
        }
    }
}
