import QtQuick

Item {
    id: root

    property url source: undefined
    property var json: null
    property var viewpoint: null
    property real zoom: 1.0

    // Required for perspective transform
    // Match theoretical values in AliceVision
    // See https://github.com/alicevision/AliceVision/blob/68ab70bcbc3eb01b73dc8dea78c78d8b4778461c/src/software/utils/main_colorCheckerDetection.cpp#L47
    readonly property real ccheckerSizeX: 1675.0
    readonly property real ccheckerSizeY: 1125.0

    property var ccheckers: []
    property int selectedCChecker: -1

    Component.onCompleted: { readSourceFile() }
    onSourceChanged: { readSourceFile() }
    onViewpointChanged: { loadCCheckers() }
    property var updatePane: null

    function getColors() {
        if (ccheckers[selectedCChecker] === undefined)
            return null

        if (ccheckers[selectedCChecker].colors === undefined)
            return null

        return ccheckers[selectedCChecker].colors
    }

    function readSourceFile() {
        var xhr = new XMLHttpRequest
        xhr.open("GET", root.source)

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE && xhr.status == 200) {
                try {
                    root.json = null
                    root.json = JSON.parse(xhr.responseText)
                } catch(exc) {
                    console.warn("Failed to parse ColorCheckerDetection JSON file: " + source)
                    return
                }
            }
            loadCCheckers()
        }
        xhr.send()
    }

    function loadCCheckers() {
        emptyCCheckers()
        if (root.json === null) {
            return
        }

        var currentImagePath = (root.viewpoint && root.viewpoint.attribute && root.viewpoint.attribute.childAttribute("path"))
                               ? root.viewpoint.attribute.childAttribute("path").value : null
        var viewId = (root.viewpoint && root.viewpoint.attribute && root.viewpoint.attribute.childAttribute("viewId"))
                     ? root.viewpoint.attribute.childAttribute("viewId").value : null

        for (var i = 0; i < root.json.checkers.length; i++) {
            // Only load ccheckers for the current view
            var checker = root.json.checkers[i]
            if (checker.viewId === viewId ||
                checker.imagePath === currentImagePath) {
                var cpt = Qt.createComponent("ColorCheckerEntity.qml")

                var obj = cpt.createObject(root, {
                    x: ccheckerSizeX / 2,
                    y: ccheckerSizeY / 2,
                    sizeX: root.ccheckerSizeX,
                    sizeY: root.ccheckerSizeY,
                    colors: root.json.checkers[i].colors
                })
                obj.applyTransform(root.json.checkers[i].transform)
                ccheckers.push(obj)
                selectedCChecker = ccheckers.length - 1
                break
            }
        }
        updatePane()
    }

    function emptyCCheckers() {
        for (var i = 0; i < ccheckers.length; i++)
            ccheckers[i].destroy()
        ccheckers = []
        selectedCChecker = -1
    }
}
