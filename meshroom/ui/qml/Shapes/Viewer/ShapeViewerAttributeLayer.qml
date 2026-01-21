import QtQuick

/**
* ShapeViewerAttributeLayer
*
* @biref Shape attribute layer loader.
* @param shapeAttribute - the given shape attribute
* @param isLinkChild - Whether the given attribute is a child of a linked attribute
* @param scaleRatio - the container scale ratio (scroll zoom)
*/
Loader {

    // Properties
    property var shapeAttribute
    property bool isLinkChild: false
    property real scaleRatio: 1.0

    // Source component
    sourceComponent: shapeAttributeLayerComponent

    // Reload source component
    // When attribute observations changed (signal)
    // For now, ShapeLayer should be re-build when observation changed
    Connections {
        target: shapeAttribute.geometry
        function onObservationsChanged() {
            sourceComponent = null
            sourceComponent = shapeAttributeLayerComponent
        }
    }

    // Shape attribute layer component
    Component {
        id: shapeAttributeLayerComponent
        Loader {
            sourceComponent: ShapeViewerLayer {
                scaleRatio: shapeViewer.scaleRatio
                name: shapeAttribute.fullName
                type: shapeAttribute.type
                properties: ({"color" : shapeAttribute.userColor, "userName" : shapeAttribute.userName})
                observation: shapeAttribute.geometry.getObservation(_currentScene ? _currentScene.selectedViewId : "-1")
                editable: shapeAttribute.enabled && !shapeAttribute.isLink && !isLinkChild
            }
        }
    }
}

