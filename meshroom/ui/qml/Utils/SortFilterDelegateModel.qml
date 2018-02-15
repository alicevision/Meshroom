import QtQuick 2.9
import QtQml.Models 2.2
import QtQuick.Controls 2.3

/**
 * SortFilderDelegateModel adds sorting and filtering capabilities on a source model.
 *
 * Filter only works on string properties for now.
 * Based on http://doc.qt.io/qt-5/qtquick-tutorials-dynamicview-dynamicview4-example.html
 */
DelegateModel {
    id: sortFilterModel

    property string sortRole: "name"            /// the role to use for sorting
    property int sortOrder: Qt.AscendingOrder   /// the sorting order
    property string filterRole: ""              /// the role to use for filtering
    property string textFilter: ""              /// the text used as filter

    onSortRoleChanged: invalidateSort()
    onSortOrderChanged: invalidateSort()
    onFilterRoleChanged: invalidateFilter()
    onTextFilterChanged: invalidateFilter()

    // display "filtered" group
    filterOnGroup: "filtered"
    // don't include elements in "items" group by default
    // as they must fall in the "unsorted" group
    items.includeByDefault: false

    groups: [
        // Group for temporarily storing items before sorting
        DelegateModelGroup {
            id: unsortedItems

            name: "unsorted"
            includeByDefault: true
            // if the source model changes, perform sorting and filtering
            onChanged: {
                sort()
                invalidateFilter()
            }
        },
        // Group for storing filtered items
        DelegateModelGroup {
            id: filteredItems
            name: "filtered"
        }
    ]

    property var lessThan: [
        function(left, right) { return left[sortRole] < right[sortRole] }
    ]

    function invalidateSort() {
        if(!sortFilterModel.model)
            return;

        // move everything from "items" to "unsorted
        // will trigger "unsorted" DelegateModelGroup 'changed' signal
        items.setGroups(0, items.count, ["unsorted"])
    }

    // TODO: add option for case sensitivity / whole word
    function containsText(reference, text)
    {
        return reference.toLowerCase().search(text.toLowerCase()) >= 0
    }

    /// Invalidate filtering
    function invalidateFilter() {
        // no filtering, add everything to the filtered group
        if(!filterRole)
        {
            items.addGroups(0, items.count, "filtered")
            return
        }

        for(var i=0; i < items.count; ++i)
        {
            // if the property value contains filterText, add it to the filtered group
            if(containsText(items.get(i).model[filterRole], textFilter))
            {
                items.addGroups(items.get(i), 1, "filtered")
            }
            else // otherwise, remove it from the filtered group
            {
                items.removeGroups(items.get(i), 1, "filtered")
            }
        }
    }

    /// Compute insert position of 'item' based on the value
    /// of its sortProperty
    function insertPosition(lessThan, item) {
        var lower = 0
        var upper = items.count
        while (lower < upper) {
            var middle = Math.floor(lower + (upper - lower) / 2)
            var result = lessThan(item.model, items.get(middle).model)
            if(sortOrder == Qt.DescendingOrder)
                result = !result
            if (result) {
                upper = middle
            } else {
                lower = middle + 1
            }
        }
        return lower
    }

    /// Perform model sorting
    function sort() {
        while (unsortedItems.count > 0) {
            var item = unsortedItems.get(0)
            var index = insertPosition(lessThan[0], item)
            item.groups = ["items"]
            items.move(item.itemsIndex, index)
        }
        // if some items were actually sorted, filter will be correctly invalidated
        // as unsortedGroup 'changed' signal will be triggered
    }

}
