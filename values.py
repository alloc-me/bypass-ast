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


def _add(a, b):
    if isinstance(a, String):
        if not isinstance(b, String):
            check_int(b)
        return String(list(a) + list(map(ord, format_value(b))))
    check_int(b)
    check_int(a)
    return a + b


BINOPS = {
    "+":  _add,
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

# У плюса собственная проверка: строка + строка/число либо число + число.
ARITH_OPS = {"-", "*", "/", "%"}


class String(list):
    pass


class Sexp:
    def __init__(self, name, args):
        self.name = name
        self.args = list(args)

    def __eq__(self, other):
        return isinstance(other, Sexp) and self.name == other.name and self.args == other.args


def format_value(value):
    if isinstance(value, String):
        return "".join(map(chr, value))
    if isinstance(value, list):
        return "[" + "; ".join(map(format_value, value)) + "]"
    if isinstance(value, Sexp):
        items = []
        tail = value
        while isinstance(tail, Sexp) and tail.name == "cons" and len(tail.args) == 2:
            items.append(format_value(tail.args[0]))
            tail = tail.args[1]
        if isinstance(tail, Sexp) and tail.name == "nil" and not tail.args:
            return "{" + ", ".join(items) + "}"
        if not value.args:
            return value.name
        return value.name + " (" + ", ".join(map(format_value, value.args)) + ")"
    return str(value)

def check_int(value):
    if not isinstance(value, int):
        raise LanguageError(f'integer value expected but "{format_value(value)}" given')
    return value

def check_array(value):
    if not isinstance(value, list):
        raise LanguageError(f'array/string value expected but "{format_value(value)}" given')
    return value


def get_items(value):
    if isinstance(value, Sexp):
        return value.args
    return check_array(value)


def check_index(array, index):
    check_int(index)
    if not 0 <= index < len(array):
        raise LanguageError(f"index {index} is out of bounds [0, {len(array)})")
    return index


def match_type(pattern, value):
    if pattern == "#int":
        return isinstance(value, int)
    if pattern == "#array":
        return type(value) is list
    if pattern == "#string":
        return isinstance(value, String)
    if pattern == "#sexp":
        return isinstance(value, Sexp)
    if isinstance(pattern, list) and len(pattern) == 3 and pattern[0] == "Tag":
        return isinstance(value, Sexp) and value.name == pattern[1] and len(value.args) == pattern[2]
    raise LanguageError(f"unknown type pattern: {pattern!r}")


def match_pattern(pattern, value):
    if isinstance(pattern, int):
        return {} if isinstance(value, int) and value == pattern else None
    if isinstance(pattern, str):
        if pattern in ("#int", "#array", "#string", "#sexp"):
            matches = match_type(pattern, value)
        else:
            matches = isinstance(value, String) and value == list(map(ord, pattern))
        return {} if matches else None
    if not isinstance(pattern, dict):
        raise LanguageError(f"unknown pattern: {pattern!r}")
    if "wildcard" in pattern:
        return {}
    if "bind" in pattern:
        binding = pattern["bind"]
        bindings = match_pattern(binding["pattern"], value)
        if bindings is not None:
            bindings[binding["name"]] = value
        return bindings
    if "array" in pattern:
        if type(value) is not list:
            return None
        patterns = pattern["array"]
        items = value
    elif "sexp" in pattern:
        if not isinstance(value, Sexp) or value.name != pattern["sexp"]:
            return None
        patterns = pattern["args"]
        items = value.args
    else:
        raise LanguageError(f"unknown pattern: {pattern!r}")
    if len(patterns) != len(items):
        return None
    bindings = {}
    for part, item in zip(patterns, items):
        found = match_pattern(part, item)
        if found is None:
            return None
        bindings.update(found)
    return bindings


def bind_variables(state, bindings):
    saved = {}

    for name in bindings:
        existed = name in state
        old_value = state.get(name)
        saved[name] = (existed, old_value)
    state.update(bindings)
    return saved


def restore_variables(state, saved):
    for name, (existed, value) in saved.items():
        if existed:
            state[name] = value
        else:
            del state[name]
