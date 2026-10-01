import QtQml
import meshViewer

/**
Represent a DepthmapLayer in the Scene Objects Collection
This is only a Delegate to keep track of the DepthmapLayers
*/
QtObject {
    id: root

    required property string source

    property DepthmapLayer depthmapLayer: DepthmapLayer {
        source: root.source
    }
}
