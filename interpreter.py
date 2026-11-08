import json
import sys

from input_parser import parse_input
from values import (
    ARITH_OPS, BINOPS, InterpreterError, LanguageError, String,
    check_array, check_index, check_int, format_value,
)


def eval_expr(expression, state):
    if "const" in expression:
        return int(expression["const"])
    if "var" in expression:
        name = expression["var"]
        if name not in state:
            raise InterpreterError(f"undefined variable {name}")
        return state[name]
    if "string" in expression:
        return String(ord(ch) for ch in expression["string"])
    if "array" in expression:
        return [eval_expr(item, state) for item in expression["array"]]
    if "elem" in expression:
        array = check_array(eval_expr(expression["elem"], state))
        index = eval_expr(expression["index"], state)
        return array[check_index(array, index)]
    if "length" in expression:
        return len(check_array(eval_expr(expression["length"], state)))
    if "binop" in expression:
        op = expression["binop"]
        if op not in BINOPS:
            raise InterpreterError(f"unknown operator {op}")
        left = eval_expr(expression["left"], state)
        right = eval_expr(expression["right"], state)
        if op in ARITH_OPS:
            check_int(right)
            check_int(left)
        return BINOPS[op](left, right)
    raise InterpreterError(f"unknown expression: {json.dumps(expression)}")

class Interpreter:
    def __init__(self, inputs):
        self.state = {}
        self.inputs = list(inputs)
        self.pos = 0
        self.output = []

    def run(self, statement):
        if statement == "skip":
            return
        if not isinstance(statement, dict) or len(statement) != 1:
            raise InterpreterError(f"unknown statement: {json.dumps(statement)}")
        [(kind, arg)] = statement.items()

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
    except LanguageError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 1
    print("; ".join(interpreter.output))
    return 0

if __name__ == "__main__":
    sys.setrecursionlimit(100_000)
    sys.exit(main())
