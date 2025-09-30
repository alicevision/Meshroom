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
        var [_res, _err] = _reconstruction.evaluateMathExpression(_text)
        if (_err == false) {
            if (isInt)
                _res = Math.round(_res)
            else
                _res = _res.toFixed(decimals)
            return _res
        } else {
            console.error("Error evaluating expression (", _text, "):", _err)
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
        var previousEvaluatedValue = evaluatedValue
        var result = getEvalExpression(root.text)
        console.log("[ExpressionTextField] updateExpression", root.text, "->", result)
        if (!isNaN(result)) {
            evaluatedValue = result
            clearError()
            // return result
        } else {
            evaluatedValue = previousEvaluatedValue
            raiseError()
            // return NaN
        }
    }

    // When user commits input, evaluate but do NOT overwrite text
    onAccepted: {
        console.log("[ExpressionTextField] onAccepted", root.text)
        updateExpression()
    }

    onEditingFinished: {
        console.log("[ExpressionTextField] onEditingFinished", root.text)
        updateExpression()
    }

    onTextChanged: {
        if (!activeFocus) {
            refreshStatus()
        }
    }

    Component.onCompleted: {
        console.log("[ExpressionTextField] onCompleted", root.text)
        refreshStatus()
    }
}
