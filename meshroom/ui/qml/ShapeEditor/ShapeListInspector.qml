import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MaterialIcons 2.2
import Controls 1.0
import Utils 1.0

/**
* ShapeListInspector
*
* @biref Repeater to create shape controls based on the given ShapeList model.
* @param model - the given ShapeList model
*/
Repeater  {
    id: shapeListInspector

    delegate: RowLayout {
        Layout.leftMargin: 2
        Layout.rightMargin: 10

        // shape visibility
        MaterialToolButton {
            font.pointSize: 8
            padding: 4
            text: (model.isVisible) ? MaterialIcons.visibility : MaterialIcons.visibility_off
            enabled: true
            onClicked: shapeListInspector.model.updateShapeVisibility(model.modelIndex, !model.isVisible)
        }

        // shape color
        Rectangle {
            color: model.properties.color
            height: 10
            width: 10
        }

        // shape type
        MaterialLabel {
            function getIcon() {
                if (model.shapeType === "point2d")    return MaterialIcons.control_camera;
                if (model.shapeType === "line")       return MaterialIcons.horizontal_rule;
                if (model.shapeType === "circle")     return MaterialIcons.radio_button_unchecked;
                if (model.shapeType === "rectangle")  return MaterialIcons.crop_5_4;
                if (model.shapeType === "text")       return MaterialIcons.title;
                return MaterialIcons.question_mark;
            }
            font.pointSize: 10
            text: getIcon()
        }

        // shape name
        Label {
            text: model.shapeName
            font.pointSize: 8
            bottomPadding: 2
            Layout.fillWidth: true
        }

        // shape observation add / remove 
        MaterialToolButton {
            font.pointSize: 8
            padding: 4
            width: 20
            height:20
            text: (model.observation === undefined) ? MaterialIcons.add : MaterialIcons.clear
            visible: model.isEditable
            Rectangle {
                anchors.fill: parent
                color: (model.observation === undefined) ? "#3300ff00" : "#33ff0000"
            }
        }

        // shape locked
        MaterialLabel {
            font.pointSize: 8
            padding: 4
            width: 20
            height:20
            opacity: 0.4
            text: MaterialIcons.lock
            visible: !model.isEditable
        }
    }
}