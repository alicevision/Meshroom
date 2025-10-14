import QtQuick

import "Items" as ShapeEditorItems

/**
* ShapeEditorItem
*
* @biref ShapeEditor item loader.
* Choose the correct component for each models
* @param model - the given ShapeAttribute / ShapeListAttribute / ShapeFile
*/
Loader {
    id: itemLoader

    // Properties
    property var model: null

    // Source component
    sourceComponent: {
        switch(itemLoader.model.type) {
            case "ShapeFile": return shapeFileComponent
            case "ShapeList": return shapeListAttributeComponent
            default:          return shapeAttributeComponent
        }
    }

    // ShapeFile component
    Component { 
        id: shapeFileComponent
        ShapeEditorItems.ShapeFileItem { shapeFile: itemLoader.model }
    }

    // ShapeListAttribute component
    Component { 
        id: shapeListAttributeComponent
        ShapeEditorItems.ShapeListAttributeItem { shapeListAttribute: itemLoader.model }
    }

    // ShapeAttribute component
    Component { 
        id: shapeAttributeComponent; 
        ShapeEditorItems.ShapeAttributeItem { shapeAttribute: itemLoader.model } 
    }
}
