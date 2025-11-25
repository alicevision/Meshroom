#!/usr/bin/env python

import ast, math


class MathEvaluator:
    """ Evaluate math expressions

    ..code::py
        # Example usage
        mev = MathEvaluator()
        print(mev.evaluate("e-1+cos(2*pi)"))
        print(mev.evaluate("pow(2, 8)"))
        print(mev.evaluate("round(sin(pi), 3)"))
    """

    # Allowed math symbols
    allowed_symbols = {
        "e": math.e, "pi": math.pi,
        "cos": math.cos, "sin": math.sin, "tan": math.tan, "exp": math.exp,
        "pow": pow, "round": round, "abs": abs, "min": min, "max": max,
        "sqrt": math.sqrt, "log": math.log
    }

    # Allowed AST node types
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Load,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
        ast.USub, ast.UAdd, ast.BitXor, ast.BitOr, ast.BitAnd,
        ast.LShift, ast.RShift, ast.Invert,
        ast.Constant
    )

    def _validate_ast(self, node):
        for child in ast.walk(node):
            if not isinstance(child, self.allowed_nodes):
                raise ValueError(f"Bad expression: {ast.dump(child)}")
            # Check that all variable/function names are whitelisted
            if isinstance(child, ast.Name):
                if child.id not in self.allowed_symbols:
                    raise ValueError(f"Unknown symbol: {child.id}")

    def evaluate(self, expr: str):
        if any(bad in expr for bad in ('\n', '#')):
            raise ValueError(f"Invalid expression: {expr}")
        try:
            node = ast.parse(expr.strip(), mode="eval")
            self._validate_ast(node)
            return eval(compile(node, "<expr>", "eval"), {"__builtins__": {}}, self.allowed_symbols)
        except Exception:
            raise ValueError(f"Invalid expression: {expr}")
