import json
import re
import sys

class InterpreterError(Exception):
    pass

def _div(a, b):
    if b == 0:
        raise InterpreterError("division by zero")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q

def _mod(a, b):
    if b == 0:
        raise InterpreterError("division by zero")
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
        raise InterpreterError(f'integer value expected but "{format_value(value)}" given')
    return value

def check_array(value):
    if not isinstance(value, list):
        raise InterpreterError(f'array/string value expected but "{format_value(value)}" given')
    return value

def check_index(array, index):
    check_int(index)
    if not 0 <= index < len(array):
        raise InterpreterError(f"index {index} is out of bounds [0, {len(array)})")
    return index

def eval_expr(e, state):
    if "const" in e:
        return int(e["const"])
    if "var" in e:
        name = e["var"]
        if name not in state:
            raise InterpreterError(f"undefined variable {name}")
        return state[name]
    if "string" in e:
        return String(ord(ch) for ch in e["string"])
    if "array" in e:
        return [eval_expr(item, state) for item in e["array"]]
    if "elem" in e:
        array = check_array(eval_expr(e["elem"], state))
        index = eval_expr(e["index"], state)
        return array[check_index(array, index)]
    if "length" in e:
        return len(check_array(eval_expr(e["length"], state)))
    if "binop" in e:
        op = e["binop"]
        if op not in BINOPS:
            raise InterpreterError(f"unknown operator {op}")
        left = eval_expr(e["left"], state)
        right = eval_expr(e["right"], state)
        if op in ARITH_OPS:
            check_int(right)
            check_int(left)
        return BINOPS[op](left, right)
    raise InterpreterError(f"unknown expression: {json.dumps(e)}")

class Interpreter:
    def __init__(self, inputs):
        self.state = {}
        self.inputs = list(inputs)
        self.pos = 0
        self.output = []

    def run(self, s):
        if s == "skip":
            return
        if not isinstance(s, dict) or len(s) != 1:
            raise InterpreterError(f"unknown statement: {json.dumps(s)}")
        (kind, arg), = s.items()

        if kind == "assn":
            self.state[arg["dst"]] = eval_expr(arg["src"], self.state)

        elif kind == "set":
            array = check_array(eval_expr(arg["dst"], self.state))
            index = eval_expr(arg["idx"], self.state)
            value = eval_expr(arg["value"], self.state)
            array[check_index(array, index)] = value

        elif kind == "read":
            if self.pos >= len(self.inputs):
                raise InterpreterError("input is exhausted")
            self.state[arg] = self.inputs[self.pos]
            self.pos += 1

        elif kind == "write":
            self.output.append(format_value(eval_expr(arg, self.state)))

        elif kind == "seq":
            self.run(arg["left"])
            self.run(arg["right"])

        elif kind == "if":
            if eval_expr(arg["cond"], self.state) != 0:
                self.run(arg["then"])
            else:
                self.run(arg["else"])

        elif kind == "while":
            while eval_expr(arg["cond"], self.state) != 0:
                self.run(arg["body"])

        elif kind == "do":
            while True:
                self.run(arg["body"])
                if eval_expr(arg["cond"], self.state) == 0:
                    break

        else:
            raise InterpreterError(f"unknown statement: {kind}")

INPUT_TOKEN_RE = re.compile(r'\s*(\[|\]|[,;]|-?[0-9]+|"[^"]*")')

def parse_input(text):
    text = text.strip()
    tokens = []
    pos = 0
    while pos < len(text):
        m = INPUT_TOKEN_RE.match(text, pos)
        if not m:
            raise InterpreterError(f"bad input at position {pos}")
        tokens.append(m.group(1))
        pos = m.end()
    values = []
    rest = read_values(tokens, values)
    if rest:
        raise InterpreterError(f"unexpected {rest[0]!r} in input")
    return values

def read_values(tokens, values):
    while tokens and tokens[0] != "]":
        if values and tokens[0] in (",", ";"):
            tokens = tokens[1:]
        value, tokens = read_value(tokens)
        values.append(value)
    return tokens

def read_value(tokens):
    if not tokens:
        raise InterpreterError("unexpected end of input")
    token, tokens = tokens[0], tokens[1:]
    if token == "[":
        items = []
        while tokens and tokens[0] != "]":
            if items and tokens[0] in (",", ";"):
                tokens = tokens[1:]
            value, tokens = read_value(tokens)
            items.append(value)
        if not tokens:
            raise InterpreterError("unterminated array in input")
        return items, tokens[1:]
    if token.startswith('"'):
        return String(map(ord, token[1:-1])), tokens
    if token in ("]", ",", ";"):
        raise InterpreterError(f"unexpected {token!r} in input")
    return int(token), tokens

def main():
    if len(sys.argv) < 2:
        print("usage: python3 interpreter.py program.json [input]", file=sys.stderr)
        return 1
    with open(sys.argv[1], encoding="utf-8") as f:
        ast = json.load(f)
    raw = sys.argv[2] if len(sys.argv) > 2 else ""

    try:
        interpreter = Interpreter(parse_input(raw))
        interpreter.run(ast)
    except InterpreterError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 1
    print("; ".join(interpreter.output))
    return 0

if __name__ == "__main__":
    sys.setrecursionlimit(100_000)
    sys.exit(main())