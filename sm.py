import json
import sys

from main import (ARITH_OPS, BINOPS, InterpreterError, String,
                  check_array, check_index, check_int, format_value, parse_input)


def normalize(instr):
    if isinstance(instr, str):
        return instr, None
    if isinstance(instr, dict) and len(instr) == 1:
        (op, arg), = instr.items()
        return op, arg
    raise InterpreterError(f"unknown instruction: {json.dumps(instr)}")


class StackMachine:
    def __init__(self, inputs):
        self.stack = []
        self.state = {}
        self.inputs = list(inputs)
        self.pos = 0
        self.output = []

    def pop(self, op):
        if not self.stack:
            raise InterpreterError(f"stack underflow at {op}")
        return self.stack.pop()

    def run(self, program):
        code = [normalize(instr) for instr in program]

        labels = {}
        for i, (op, arg) in enumerate(code):
            if op == "LABEL":
                labels[arg] = i

        def target(arg, op):
            if arg not in labels:
                raise InterpreterError(f"unknown label {arg} at {op}")
            return labels[arg]

        pc = 0
        while pc < len(code):
            op, arg = code[pc]
            pc += 1

            if op == "LABEL":
                continue
            elif op == "CONST":
                self.stack.append(int(arg))
            elif op == "LD":
                if arg not in self.state:
                    raise InterpreterError(f"undefined variable {arg}")
                self.stack.append(self.state[arg])
            elif op == "ST":
                self.state[arg] = self.pop(op)
            elif op == "READ":
                if self.pos >= len(self.inputs):
                    raise InterpreterError("input is exhausted")
                self.stack.append(self.inputs[self.pos])
                self.pos += 1
            elif op == "WRITE":
                self.output.append(format_value(self.pop(op)))
            elif op == "BINOP":
                if arg not in BINOPS:
                    raise InterpreterError(f"unknown operator {arg}")
                right = self.pop(op)
                left = self.pop(op)
                if arg in ARITH_OPS:
                    check_int(right)
                    check_int(left)
                self.stack.append(BINOPS[arg](left, right))
            elif op == "ARRAY":
                size = int(arg)
                if size > len(self.stack):
                    raise InterpreterError(f"stack underflow at {op}")
                items = self.stack[len(self.stack) - size:]
                del self.stack[len(self.stack) - size:]
                self.stack.append(items)
            elif op == "STRING":
                self.stack.append(String(map(ord, arg)))
            elif op == "LENGTH":
                self.stack.append(len(check_array(self.pop(op))))
            elif op == "ELEM":
                index = self.pop(op)
                array = check_array(self.pop(op))
                self.stack.append(array[check_index(array, index)])
            elif op == "SET":
                value = self.pop(op)
                index = self.pop(op)
                array = check_array(self.pop(op))
                array[check_index(array, index)] = value
            elif op == "JMP":
                pc = target(arg, op)
            elif op == "JZ":
                if self.pop(op) == 0:
                    pc = target(arg, op)
            elif op == "JNZ":
                if self.pop(op) != 0:
                    pc = target(arg, op)
            else:
                raise InterpreterError(f"unknown instruction {op}")


def main():
    if len(sys.argv) < 2:
        print("usage: python3 sm.py program.json [input]", file=sys.stderr)
        return 1
    with open(sys.argv[1], encoding="utf-8") as f:
        program = json.load(f)
    raw = sys.argv[2] if len(sys.argv) > 2 else ""

    try:
        m = StackMachine(parse_input(raw))
        m.run(program)
    except InterpreterError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 1
    print("; ".join(m.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
