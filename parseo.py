import re
from sympy import sympify


def normalize_expression(expression):
    # Mapeo de superíndices Unicode a sus equivalentes con ^
    unicode_superscript_map = {
        "²": "^2", "³": "^3", "⁴": "^4", "⁵": "^5",
        "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9", "¹": "^1",
        "⁰": "^0"
    }

    # Reemplazar superíndices Unicode por ^n
    expression = re.sub(
        r"[²³⁴⁵⁶⁷⁸⁹¹⁰]", lambda m: unicode_superscript_map.get(m.group(0), m.group(0)),
        expression
    )

    # Realizar otros reemplazos de una sola vez
    expression = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", expression)  # 2x → 2*x
    expression = re.sub(r"([a-zA-Z])(\d)", r"\1*\2", expression)  # x2 → x*2
    expression = re.sub(r"\)\(", r")*(", expression)  # )( → )*(
    expression = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", expression)
    expression = re.sub(r"\\text\{([^}]*)\}", r"\1", expression)  # Remueve \text{}
    
    # Eliminar espacios extra y barras invertidas
    expression = expression.replace(" ", "").replace("\\", "")

    return expression


