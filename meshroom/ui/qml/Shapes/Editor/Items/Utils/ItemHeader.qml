import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import MaterialIcons 2.2
import Controls 1.0
import Utils 1.0

/**
* ItemHeader
*
* @biref Item header component for the ShapeEditor.
* @param model - the given model (provide by the current node or ShapeFilesHelper)
* @param isShape - whether the model is a shape (ShapeAttribute or ShapeData)
* @param isAttribute - whether the model is an attribute (ShapeAttribute or ShapeListAttribute)
* @param isNeasted - whether the header is neasted
* @param isLinkChild - Whether the model is a child attribute of a linked attribute
* @param isExpanded - whether the heder is expanded
*/
Pane {
    id: itemHeader
    width: parent.width

    // Model properties
    property var model
    property bool isShape: false
    property bool isAttribute: false
    property bool isLinkChild: false

    // Header properties
    property bool isNeasted: false
    property bool isExpanded: false

    // Read-only properties
    readonly property bool isAttributeSelected: isAttribute ? (ShapeViewerHelper.selectedShapeName === model.fullName) : false
    readonly property bool isAttributeInitialized: isAttribute ? (isShape ? !model.geometry.isDefault : !model.isDefault) : false
    readonly property bool isAttributeEnabled: isAttribute ? (model.enabled && !model.isLink && !isLinkChild) : false

    // Padding
    topPadding: 2
    bottomPadding: 2
    rightPadding: 6
    leftPadding: 6

    // Background
    background: Rectangle { 
        radius: 3
        border.color: palette.highlight
        border.width: {
            if(isAttributeSelected)
                return 2
            return 0
        }
        color: {
            if(isAttributeSelected)
                return palette.window
            if(hoverHandler.hovered) 
                return Qt.darker(palette.window, 1.1)
            return "transparent" 
        }

        SequentialAnimation {
            id: flickAnimation
            loops: 2
            
            NumberAnimation {
                target: itemHeader.background
                property: "border.width"
                to: 1
                duration: 100
            }
            NumberAnimation {
                target: itemHeader.background
                property: "border.width" 
                to: 0
                duration: 100
            }
            PauseAnimation { duration: 50 }
        }
    }

    // Item header menu
    // Popup on right mouse button 
    Menu {
        id: itemHeaderMenu
        MenuItem {
            text: "Reset"
            enabled: isAttributeEnabled && isAttributeInitialized
            onTriggered: {
                _currentScene.resetAttribute(model)
                ShapeViewerHelper.selectedShapeName = ""
                isExpanded = false
            }
        }
    }

    // Hover Handle
    HoverHandler { 
        id: hoverHandler
        margin: 3
    }

    // Tap Handler
    // Left and Right mouse button handler
    TapHandler {
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        gesturePolicy: TapHandler.WithinBounds
        margin: 3
        onTapped: function(eventPoint, button) {
            // Right mouse button
            if(button === Qt.RightButton)
                itemHeaderMenu.popup()

            // Left mouse button
            if(button === Qt.LeftButton && isShape && isAttributeEnabled && isAttributeInitialized)
            {
                // Single tap
                if(tapCount === 1 && model.isVisible)
                {
                    ShapeViewerHelper.selectedShapeName = model.fullName
                }

                // Double tap
                if(tapCount === 2 && !model.isVisible)
                {
                    
                    ShapeViewerHelper.selectedShapeName = model.fullName
                    model.isVisible = true
                }
            }
            else
            {
                flickAnimation.start()
            }
        }
    }

    // MaterialIcons font metrics
    FontMetrics {
        id: materialMetrics
        font.family: MaterialIcons.fontFamily
        font.pointSize: 11
    }

    // Row layout
    RowLayout {
        anchors.fill: parent
        anchors.rightMargin: 2
        spacing: 0

        // Shape visibility
        MaterialToolButton {
            font.pointSize: 9
            padding: (materialMetrics.height / 11.0) + 2
            text: model.isVisible ? MaterialIcons.visibility : MaterialIcons.visibility_off
            opacity: model.isVisible ? 1.0 : 0.5
            enabled: true
            onClicked: { model.isVisible = !model.isVisible }
            ToolTip.text: model.isVisible ? "Visible" : "Hidden"
            ToolTip.visible: hovered
            ToolTip.delay: 800
        }

        // Neasted spacer
        // 1x icon + 2x padding
        Item {
            visible: isNeasted
            width: materialMetrics.height + 4 
        }

        // Shape attributes dropdown
        // For now, only for ShapeFile and ShapeListAttribute
        Loader {
            active: !isShape 
            sourceComponent: MaterialToolButton {
                font.pointSize: 11
                padding: 2
                text: {
                    if(isExpanded) {
                        return (isShape) ?  MaterialIcons.arrow_drop_down : MaterialIcons.keyboard_arrow_down
                    }
                    else {
                        return (isShape) ?  MaterialIcons.arrow_right : MaterialIcons.keyboard_arrow_right
                    }
                }
                onClicked: { isExpanded = !isExpanded }
                enabled: true
                ToolTip.text: isExpanded ? "Collapse" : "Expand"
                ToolTip.visible: hovered
                ToolTip.delay: 800
            }
        }

        // Shape color
        Loader {
            active: isShape 
            sourceComponent: ToolButton {
                enabled: isAttributeEnabled
                contentItem: Rectangle {
                    anchors.centerIn: parent
                    color: isAttribute ? model.userColor : model.properties.color || "black"
                    width: materialMetrics.height
                    height: materialMetrics.height
                }
                onClicked: shapeColorDialog.item.open()
                ToolTip.text: "Shape Color"
                ToolTip.visible: hovered
                ToolTip.delay: 800
            }
        }

        // Shape ColorDialog
        Loader {
            id: shapeColorDialog
            active: isShape && isAttributeEnabled
            sourceComponent: ColorDialog {
                title: "Edit " + model.label + " color"
                selectedColor: model.userColor
                onAccepted: {
                    _currentScene.setAttribute(model.childAttribute("userColor"), selectedColor.toString())
                    close()
                }
                onRejected: close()
            }
        }

        // Shape type and shape name
        RowLayout {
            spacing: 2
            opacity: (isAttributeEnabled && isAttributeInitialized) ? 1.0 : 0.7

            // Shape type
            MaterialLabel {
                font.pointSize: 11
                padding: 2
                text: {
                    switch(model.type) {
                        case "ShapeFile": return MaterialIcons.insert_drive_file;
                        case "ShapeList": return MaterialIcons.layers;
                        case "Point2d":   return MaterialIcons.control_camera;
                        case "Line2d":    return MaterialIcons.linear_scale;
                        case "Circle":    return MaterialIcons.radio_button_unchecked;
                        case "Rectangle": return MaterialIcons.crop_landscape;
                        case "Text":      return MaterialIcons.title;
                        default:          return MaterialIcons.question_mark;
                    }
                }
            }

            // Shape name
            TextField {
                font.pointSize: 8
                background: Rectangle { color: "transparent" }
                palette.text: parent.palette.text
                maximumLength: 40 
                selectByMouse: true
                persistentSelection: false
                text: {
                    if(isAttribute && isShape && model.userName)
                        return model.userName
                    if(isAttribute && model.root && (model.root.type === "ShapeList"))
                        return model.rootName
                    return model.label
                }
                enabled: isAttributeEnabled && model.root && (model.root.type === "ShapeList")
                onEditingFinished: { 
                    _currentScene.setAttribute(model.childAttribute("userName"), text)
                    focus = false
                }
            }

            // Shape file basename
            Loader {
                active: !isShape && !isAttribute && model.basename !== ""
                sourceComponent: Label {
                    font.pointSize: 8
                    text: "(" + model.basename + ")"
                }
            }

            // Shape number of observations
            Loader {
                active: isShape && (isAttribute ? model.geometry.observationKeyable : model.observationKeyable)
                sourceComponent: Label {
                    text: "(" + (isAttribute ? model.geometry.nbObservations : model.nbObservations) + ")"
                    font.pointSize: 8
                }
            }
        }

        // Spacer
        Item { Layout.fillWidth: true }

        // Right toolbar
        RowLayout {
            spacing: 0

            // Static shape, set/remove observation
            Loader {
                active: isShape && isAttribute && !model.geometry.observationKeyable
                sourceComponent: MaterialToolButton {
                    font.pointSize: 11
                    padding: 2
                    text: isAttributeInitialized ? MaterialIcons.clear : MaterialIcons.edit
                    checkable: false
                    enabled: isAttributeEnabled
                    onClicked: {
                        if(isAttributeInitialized)
                        {
                            // remove key
                            _currentScene.removeObservation(model, _currentScene.selectedViewId)
                            ShapeViewerHelper.selectedShapeName = ""
                        }
                        else
                        {
                            // add key
                            _currentScene.setObservation(model, _currentScene.selectedViewId, 
                                                          ShapeViewerHelper.getDefaultObservation(model.type))
                            ShapeViewerHelper.selectedShapeName = model.fullName
                        }
                    }
                    ToolTip.text: isAttributeInitialized ? "Reset Shape" : "Set Shape"
                    ToolTip.visible: hovered
                    ToolTip.delay: 800
                }
            }

            // Shape keyable, set/remove observation
            Loader {
                active: isShape && (isAttribute ? model.geometry.observationKeyable : model.observationKeyable)
                sourceComponent: RowLayout {
                    spacing: 0
                    property var keys: isAttribute ? model.geometry.observationKeys : model.observationKeys
                    property bool hasCurrentKey: {
                        if(isAttribute)
                            return model.geometry.hasObservation(_currentScene.selectedViewId)
                        return model.hasObservation(_currentScene.selectedViewId)
                    }

                    function getViewPath(viewId) {
                        for (var i = 0; i < _currentScene.viewpoints.count; i++) 
                        {
                            var vp = _currentScene.viewpoints.at(i)
                            if (vp.childAttribute("viewId").value == viewId) 
                                return vp.childAttribute("path").value
                        }
                        return undefined
                    }

                    function getPrevViewId(viewIds, currentViewId) {
                        const currentViewPath = getViewPath(currentViewId)
                        const prevIds = viewIds.filter(viewId => getViewPath(viewId) < currentViewPath)
                        if (prevIds.length === 0) 
                            return "-1";
                        prevIds.sort((a, b) => getViewPath(b).localeCompare(getViewPath(a)))
                        return prevIds[0]
                    }

                    function getNextViewId(viewIds, currentViewId) {
                        const currentViewPath = getViewPath(currentViewId)
                        const nextIds = viewIds.filter(viewId => getViewPath(viewId) > currentViewPath)
                        if (nextIds.length === 0) 
                            return "-1";
                        nextIds.sort((a, b) => getViewPath(a).localeCompare(getViewPath(b)))
                        return nextIds[0]
                    }

                    // Previous key
                    MaterialToolButton {
                        property string prevViewId: getPrevViewId(keys, _currentScene.selectedViewId)
                        font.pointSize: 11
                        padding: 2
                        text: MaterialIcons.keyboard_arrow_left
                        checkable: false
                        enabled: prevViewId !== "-1"
                        onClicked: { _currentScene.selectedViewId = prevViewId }
                        ToolTip.text: enabled ? "Previous Key" : "No Previous Key"
                        ToolTip.visible: hovered
                        ToolTip.delay: 800
                    }

                    // Current key
                    MaterialToolButton {
                        font.pointSize: 11
                        padding: 2
                        text: MaterialIcons.noise_control_off
                        checkable: true
                        checked: hasCurrentKey
                        enabled: isAttributeEnabled
                        onClicked: {
                            if(hasCurrentKey)
                            {
                                // remove key
                                _currentScene.removeObservation(model, _currentScene.selectedViewId)
                                ShapeViewerHelper.selectedShapeName = ""
                            }
                            else
                            {
                                // add key
                                _currentScene.setObservation(model, _currentScene.selectedViewId, 
                                                               ShapeViewerHelper.getDefaultObservation(model.type))
                                ShapeViewerHelper.selectedShapeName = model.fullName
                            }
                        }
                        ToolTip.text: checked ? "Remove current key" : "Set current key"
                        ToolTip.visible: hovered
                        ToolTip.delay: 800
                    }

                    // Next key
                    MaterialToolButton {
                        property string nextViewId: getNextViewId(keys, _currentScene.selectedViewId)
                        font.pointSize: 11
                        padding: 2
                        text: MaterialIcons.keyboard_arrow_right
                        checkable: false
                        enabled: nextViewId !== "-1"
                        onClicked: {  _currentScene.selectedViewId = nextViewId }
                        ToolTip.text: enabled ? "Next Key" : "No Next Key"
                        ToolTip.visible: hovered
                        ToolTip.delay: 800
                    }
                }
            }

            // Shape list add element
            Loader {
                active: !isShape && isAttributeEnabled
                sourceComponent: MaterialToolButton {
                    font.pointSize: 11
                    padding: 2
                    text: MaterialIcons.control_point
                    onClicked: _currentScene.appendAttribute(model, undefined)
                    ToolTip.text: "Add Element"
                    ToolTip.visible: hovered
                    ToolTip.delay: 800
                }
            }

            // Shape list delete element
            Loader {
                active: isAttributeEnabled && model.root && (model.root.type === "ShapeList")
                sourceComponent: MaterialToolButton {
                    font.pointSize: 11
                    padding: 2
                    text: MaterialIcons.remove_circle_outline
                    onClicked: {
                        _currentScene.removeAttribute(model)
                    }
                    ToolTip.text: "Remove Element"
                    ToolTip.visible: hovered
                    ToolTip.delay: 800
                }
            }

            // Shape is a link or locked
            Loader {
                active: !isAttributeEnabled
                sourceComponent: MaterialLabel {
                    font.pointSize: 11
                    padding: 2
                    opacity: 0.4
                    text: isAttribute && (model.isLink || isLinkChild) ? MaterialIcons.link : MaterialIcons.lock
                }
            }
        }
    }
}