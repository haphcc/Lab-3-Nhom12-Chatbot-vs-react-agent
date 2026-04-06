import ast
import operator as op
from typing import Any, Callable, Dict, List


_SAFE_OPERATORS: Dict[Any, Callable[[Any, Any], Any]] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _safe_eval_math(expression: str) -> float:
    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[type(node.op)](_eval(node.operand))
        raise ValueError("Unsupported expression")

    tree = ast.parse(expression, mode="eval")
    return float(_eval(tree.body))


def calculator(expression: str) -> str:
    """Safely evaluate a basic arithmetic expression."""
    result = _safe_eval_math(expression)
    if result.is_integer():
        return str(int(result))
    return str(result)


_FACTS = {
    "capital of france": "Paris",
    "capital of vietnam": "Hanoi",
    "capital of japan": "Tokyo",
    "capital of germany": "Berlin",
    "react": "ReAct means Thought -> Action -> Observation.",
    "chatbot": "A chatbot replies directly without tool use.",
}


def knowledge_lookup(query: str) -> str:
    """Return a deterministic answer from a small demo knowledge base."""
    normalized = query.strip().lower()
    for key, value in _FACTS.items():
        if key in normalized:
            return value
    return f"No demo fact found for: {query}"


def build_demo_tools() -> List[Dict[str, Any]]:
    """Return the tool inventory used by the CLI demos."""
    return [
        {
            "name": "calculator",
            "description": "Evaluate a single arithmetic expression passed as a string, for example \"(12 + 3) * 2\".",
            "callable": calculator,
        },
        {
            "name": "knowledge_lookup",
            "description": "Look up a short fact from the demo knowledge base using one string query.",
            "callable": knowledge_lookup,
        },
    ]