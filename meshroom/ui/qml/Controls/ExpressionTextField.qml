import QtQuick
import QtQuick.Controls

TextField {
    id: root

    property bool hasExprError: false
    property bool isInt: false          // If not then it's a float

    signal expressionEditingFinished()
    signal expressionAccepted()

    // Overlay for error state
    Rectangle {
        anchors.fill: parent
        radius: 4
        border.color: "red"
        color: "transparent"
        visible: root.hasExprError || root.text == "NaN"
        z: 1
    }

    function evalExpression() {
        try {
            if (root.text == "NaN") {
                hasExprError = true
                return
            }
            var result = MathEvaluator.eval(root.text)
            if (isInt) {
                result = parseInt(result)
            } else {
                // Probably useless
                result = parseFloat(result)
            }
            root.text = result
            hasExprError = false
        } catch (err) {
            console.error("Error evaluating expression (", root.text,"):", err)
            hasExprError = true
            root.text = "NaN"
        }
    }

    onEditingFinished : {
        evalExpression()
    }

    onAccepted : {
        evalExpression()
    }
}
