import QtQuick
import QtQuick.Controls

TextField {
    id: root

    // evaluated numeric value (NaN if invalid)
    // It helps keeping the connection that text has so that we don't loose ability to undo/reset
    property real evaluatedValue: 0

    property bool hasExprError: false
    property bool isInt: false
    property int decimals: 2

    // Overlay for error state (red border on top of default background)
    Rectangle {
        anchors.fill: parent
        radius: 4
        border.color: "red"
        color: "transparent"
        visible: root.hasExprError
        z: 1
    }

    function raiseError() {
        hasExprError = true
    }

    function clearError() {
        hasExprError = false
    }

    function reset(_value) {
        clearError()
        evaluatedValue = _value
        if (isInt) {
            root.text = _value.toFixed(0)
        } else {
            root.text = _value.toFixed(decimals)
        }
    }

    function getEvalExpression(_text) {
        try {
            var result = MathEvaluator.eval(_text)
            if (isInt)
                result = Math.round(result)
            else
                result = result.toFixed(decimals)
            return result
        } catch (err) {
            console.error("Error evaluating expression (", _text, "):", err)
            return NaN
        }
    }

    function refreshStatus() {
        if (isNaN(getEvalExpression(root.text))) {
            raiseError()
        } else {
            clearError()
        }
    }

    function updateExpression() {
        var result = getEvalExpression(root.text)
        if (!isNaN(result)) {
            evaluatedValue = result
            clearError()
            return result
        } else {
            evaluatedValue = NaN
            raiseError()
            return NaN
        }
    }

    // When user commits input, evaluate but do NOT overwrite text
    onAccepted: {
        updateExpression()
    }

    onEditingFinished: {
        updateExpression()
    }

    onTextChanged: {
        if (!activeFocus) {
            refreshStatus()
        }
    }

    Component.onCompleted: {
        refreshStatus()
    }
}
