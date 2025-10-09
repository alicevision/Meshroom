import QtQuick

/**
* ShapeViewerAttributeLoader
*
* @biref ShapeViewer attribute loader.
* @param attribute - the given attribute (ShapeAttribute or ShapeListAttribute)
* @param scaleRatio - the container scale ratio (scroll zoom)
*/
Loader {
    id: attributeLoader

    // Properties
    property var attribute
    property real scaleRatio: 1.0

    // Attribute should be shape or shape list
    // Attribute should be visible
    active: attribute.hasDisplayableShape && attribute.isVisible 

    // Source component
    sourceComponent: {
        if(attribute.type === "ShapeList")
            return shapeListAttributeComponent
        return shapeAttributeComponent
    }

    // Shape attribute component
    Component {
        id: shapeAttributeComponent
        ShapeViewerAttributeLayer {
            active: !attribute.geometry.isDefault
            shapeAttribute: attribute
            scaleRatio: attributeLoader.scaleRatio
        }
    }

    // Shape list attribute component
    Component {
        id: shapeListAttributeComponent
        Repeater {
            model: attribute.value
            delegate: ShapeViewerAttributeLayer {
                active: object.isVisible && !object.geometry.isDefault
                shapeAttribute: object
                isLinkChild: attribute.isLink
                scaleRatio: attributeLoader.scaleRatio
            }
        }
    }
}