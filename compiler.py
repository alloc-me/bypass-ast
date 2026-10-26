import json
import sys

from main import InterpreterError


class Compiler:
    def __init__(self):
        self.counter = 0

    def label(self, kind):
        self.counter += 1
        return f"L_{kind}_{self.counter}"

    def expr(self, e):
        if "const" in e:
            return [{"CONST": e["const"]}]
        if "var" in e:
            return [{"LD": e["var"]}]
        if "string" in e:
            return [{"STRING": e["string"]}]
        if "array" in e:
            code = []
            for item in e["array"]:
                code += self.expr(item)
            return code + [{"ARRAY": len(e["array"])}]
        if "elem" in e:
            return self.expr(e["elem"]) + self.expr(e["index"]) + ["ELEM"]
        if "length" in e:
            return self.expr(e["length"]) + ["LENGTH"]
        return self.expr(e["left"]) + self.expr(e["right"]) + [{"BINOP": e["binop"]}]

    def stmt(self, s):
        if s == "skip":
            return []
        (kind, arg), = s.items()

        if kind == "read":
            return ["READ", {"ST": arg}]
        if kind == "write":
            return self.expr(arg) + ["WRITE"]
        if kind == "assn":
            return self.expr(arg["src"]) + [{"ST": arg["dst"]}]
        if kind == "set":
            return (self.expr(arg["dst"])
                    + self.expr(arg["idx"])
                    + self.expr(arg["value"])
                    + ["SET"])
        if kind == "seq":
            return self.stmt(arg["left"]) + self.stmt(arg["right"])

        if kind == "if":
            end = self.label("seq")
            els = self.label("else")
            return (self.expr(arg["cond"])
                    + [{"JZ": els}]
                    + self.stmt(arg["then"])
                    + [{"JMP": end}, {"LABEL": els}]
                    + self.stmt(arg["else"])
                    + [{"LABEL": end}])

        if kind == "while":
            body = self.label("while_body")
            cond = self.label("while_cond")
            return ([{"JMP": cond}, {"LABEL": body}]
                    + self.stmt(arg["body"])
                    + [{"LABEL": cond}]
                    + self.expr(arg["cond"])
                    + [{"JNZ": body}])

        if kind == "do":
            body = self.label("while_body")
            cond = self.label("while_cond")
            return ([{"LABEL": body}]
                    + self.stmt(arg["body"])
                    + [{"LABEL": cond}]
                    + self.expr(arg["cond"])
                    + [{"JNZ": body}])

        raise InterpreterError(f"unknown statement {kind!r}")


def main():
    if len(sys.argv) < 2:
        print("usage: python3 compiler.py program.json", file=sys.stderr)
        return 1
    with open(sys.argv[1], encoding="utf-8") as f:
        ast = json.load(f)

    try:
        code = Compiler().stmt(ast)
    except InterpreterError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 1

    print(json.dumps(code, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
