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
    for unicode_char, latex_equiv in unicode_superscript_map.items():
        expression = expression.replace(unicode_char, latex_equiv)

    # Asegurar que la multiplicación implícita sea explícita
    expression = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", expression)  # 2x → 2*x
    expression = re.sub(r"([a-zA-Z])(\d)", r"\1*\2", expression)  # x2 → x*2
    expression = re.sub(r"\)\(", r")*(", expression)  # )( → )*(
    
    # Convertir \frac{a}{b} a a/b
    expression = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", expression)

    # Eliminar espacios extra
    expression = expression.replace(" ", "")
    
    # Eliminar \text{} y similares si no son necesarios para la comparación
    expression = re.sub(r"\\text\{([^}]*)\}", r"\1", expression)  # Remueve \text{}
    
    # Reemplazar las barras invertidas (solo si es necesario para sympy)
    expression = expression.replace("\\", "")  # Eliminar todas las barras invertidas
    
    return expression


