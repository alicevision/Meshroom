.pragma library

function childIndex(attribute) {
    if (!attribute || !attribute.root || attribute.root.type !== "AnySet") {
        return -1
    }

    const anySetValue = attribute.root.value
    for (let i = 0; i < anySetValue.count; i++) {
        if (anySetValue.at(i) === attribute) {
            return i
        }
    }
    return -1
}

function childCount(attribute) {
    if (!attribute || !attribute.root || attribute.root.type !== "AnySet") {
        return 0
    }
    return attribute.root.value.count
}

function canMoveBy(attribute, offset) {
    const index = childIndex(attribute)
    if (index < 0) {
        return false
    }
    return index + offset >= 0 && index + offset < childCount(attribute)
}
