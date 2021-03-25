import QtQuick 2.11

Item {
    id: root

    property url source: undefined
    property var sourceLastModified: null
    property var json: null
    property var image: null
    property var viewId: null
    property real zoom: 1.0

    // required for perspective transform
    readonly property real ccheckerSizeX: 1675.0
    readonly property real ccheckerSizeY: 1125.0

    // offset the cchecker top left corner to match the image top left corner
    x: -image.width / 2 + ccheckerSizeX / 2
    y: -image.height / 2 + ccheckerSizeY / 2

    property var ccheckers: []
    property int selectedCChecker: -1


    onVisibleChanged: { readSourceFile(); }
    onSourceChanged: { readSourceFile(); }
    onViewIdChanged: { loadCCheckers(); }
    property var updatePane: null

    function readSourceFile() {
        var xhr = new XMLHttpRequest;
        xhr.open("GET", root.source);

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE && xhr.status == 200) {

                if(root.sourceLastModified === null
                   || root.sourceLastModified < xhr.getResponseHeader('Last-Modified')
                  ) {
                    try {
                        root.json = JSON.parse(xhr.responseText);
                    }
                    catch(exc)
                    {
                        console.warn("Failed to parse ColorCheckerDetection JSON file: " + source);
                        return;
                    }
                    root.sourceLastModified = xhr.getResponseHeader('Last-Modified');
                    loadCCheckers();
                }
            }
        };
        xhr.send();
    }

    function loadCCheckers() {
        if (root.json === null)
            return;

        emptyCCheckers();

        for (var i = 0; i < root.json.checkers.length; i++) {
            // Only load ccheckers for the current view
            if (root.viewId == root.json.checkers[i].viewId) {
                var cpt = Qt.createComponent("ColorCheckerEntity.qml");

                var obj = cpt.createObject(root, {
                    sizeX: root.ccheckerSizeX,
                    sizeY: root.ccheckerSizeY,
                    colors: root.json.checkers[i].colors
                });
                obj.transform(root.json.checkers[i].transform);
                ccheckers.push(obj);
                selectedCChecker = ccheckers.length-1;
            }
        }
        updatePane();
    }

    function emptyCCheckers() {
        for (var i = 0; i < ccheckers.length; i++)
            ccheckers[i].destroy();
        ccheckers = [];
        selectedCChecker = -1;
    }

}
