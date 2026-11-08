class LanguageError(Exception):
    pass


class InterpreterError(LanguageError):
    pass


class CompilerError(LanguageError):
    pass


class StackMachineError(LanguageError):
    pass


def _div(a, b):
    if b == 0:
        raise LanguageError("division by zero")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q

def _mod(a, b):
    if b == 0:
        raise LanguageError("division by zero")
    return a - _div(a, b) * b

BINOPS = {
    "+":  lambda a, b: a + b,
    "-":  lambda a, b: a - b,
    "*":  lambda a, b: a * b,
    "/":  _div,
    "%":  _mod,
    "==": lambda a, b: int(a == b),
    "!=": lambda a, b: int(a != b),
    "<":  lambda a, b: int(a < b),
    "<=": lambda a, b: int(a <= b),
    ">":  lambda a, b: int(a > b),
    ">=": lambda a, b: int(a >= b),
    "&&": lambda a, b: int(a != 0 and b != 0),
    "!!": lambda a, b: int(a != 0 or b != 0),
}

ARITH_OPS = {"+", "-", "*", "/", "%"}

class String(list):
    pass

def format_value(value):
    if isinstance(value, String):
        return "".join(map(chr, value))
    if isinstance(value, list):
        return "[" + "; ".join(map(format_value, value)) + "]"
    return str(value)

def check_int(value):
    if not isinstance(value, int):
        raise LanguageError(f'integer value expected but "{format_value(value)}" given')
    return value

def check_array(value):
    if not isinstance(value, list):
        raise LanguageError(f'array/string value expected but "{format_value(value)}" given')
    return value

def check_index(array, index):
    check_int(index)
    if not 0 <= index < len(array):
        raise LanguageError(f"index {index} is out of bounds [0, {len(array)})")
    return index

