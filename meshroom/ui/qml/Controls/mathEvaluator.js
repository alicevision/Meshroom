.pragma library


var symbols = {
    pi: Math.PI,
    e: Math.E,
    abs: Math.abs,
    min: Math.min,
    max: Math.max,
    sin: Math.sin,
    cos: Math.cos,
    tan: Math.tan,
    pow: Math.pow,
    sqrt: Math.sqrt,
    exp: Math.exp,
    log: Math.log
};


/**
 * Evaluate an expression
 * 
 * @param {*} expr Math expression
 * @returns        float or int
 */
function eval(expr) {
    // Replace symbols
    for (var symbol in symbols) {
        // Match each symbol only if they are at the beginning or end of the word
        expr = expr.replace(new RegExp("\\b" + symbol + "\\b", "g"), symbols[symbol]);
    }
    
    // Additionally replace the "," to "."
    expr = expr.replace(',','.')
    
    // Only allow numbers, operators, parentheses, and function names
    if (!/^[0-9+\-*/^().,\s]*$/.test(expr.replace(/\b[a-zA-Z]+\b/g, ""))) {
        throw "Invalid characters in expression";
    }

    // Eval with function to avoid issues with undeclared variables
    return Function('"use strict"; return (' + expr + ')')();
}
