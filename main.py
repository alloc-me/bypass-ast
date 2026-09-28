import json
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

def eval_expr(e, state):
    if "const" in e:
        return int(e["const"])
    if "var" in e:
        name = e["var"]
        if name not in state:
            raise InterpreterError(f"undefined variable {name}")
        return state[name]
    if "binop" in e:
        op = e["binop"]
        if op not in BINOPS:
            raise InterpreterError(f"unknown operator {op}")
        left = eval_expr(e["left"], state)
        right = eval_expr(e["right"], state)
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

        elif kind == "read":
            if self.pos >= len(self.inputs):
                raise InterpreterError("input is exhausted")
            self.state[arg] = self.inputs[self.pos]
            self.pos += 1

        elif kind == "write":
            self.output.append(eval_expr(arg, self.state))

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

def parse_input(text):
    try:
        return [int(val) for val in text.split()]
    except ValueError as ex:
        raise InterpreterError(f"bad input: {ex}")

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
    print("; ".join(map(str, interpreter.output)))
    return 0

if __name__ == "__main__":
    sys.setrecursionlimit(100_000)
    sys.exit(main())