import ast
import importlib
import operator as op


def _load_simple_eval():
    """
    Lazy-import simpleeval without static import statement so IDEs
    do not raise 'Import could not be resolved' when dependency is absent.
    """
    try:
        module = importlib.import_module("simpleeval")
        return getattr(module, "simple_eval", None)
    except Exception:  # pragma: no cover - optional dependency
        return None


SIMPLE_EVAL = _load_simple_eval()


_SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _safe_eval(expression: str):
    def _evaluate(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[type(node.op)](_evaluate(node.operand))
        raise ValueError("Bieu thuc khong hop le hoac khong an toan.")

    parsed = ast.parse(expression, mode="eval")
    return _evaluate(parsed.body)


def calculate(expression: str) -> str:
    """Tinh toan bieu thuc toan hoc va tra ve string thong nhat."""
    try:
        clean_expr = expression.replace("^", "**").replace("x", "*").strip()
        if SIMPLE_EVAL is not None:
            result = SIMPLE_EVAL(clean_expr)
        else:
            result = _safe_eval(clean_expr)
        return f"Ket qua: {result}"
    except Exception as exc:
        return f"Loi tinh toan: {exc}"
