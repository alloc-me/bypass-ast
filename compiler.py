import json
import sys

from values import CompilerError, LanguageError


class Compiler:
    def __init__(self):
        self.counter = 0

    def label(self, kind):
        self.counter += 1
        return f"L_{kind}_{self.counter}"

    def expr(self, expression):
        if "const" in expression:
            return [{"CONST": expression["const"]}]
        if "var" in expression:
            return [{"LD": expression["var"]}]
        if "string" in expression:
            return [{"STRING": expression["string"]}]
        if "array" in expression:
            code = []
            for item in expression["array"]:
                code += self.expr(item)
            return code + [{"ARRAY": len(expression["array"])}]
        if "elem" in expression:
            return self.expr(expression["elem"]) + self.expr(expression["index"]) + ["ELEM"]
        if "length" in expression:
            return self.expr(expression["length"]) + ["LENGTH"]
        return self.expr(expression["left"]) + self.expr(expression["right"]) + [{"BINOP": expression["binop"]}]

    def stmt(self, statement):
        if statement == "skip":
            return []
        [(kind, arg)] = statement.items()

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
            else_label = self.label("else")
            return (self.expr(arg["cond"])
                    + [{"JZ": else_label}]
                    + self.stmt(arg["then"])
                    + [{"JMP": end}, {"LABEL": else_label}]
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

        raise CompilerError(f"unknown statement {kind!r}")


def main():
    if len(sys.argv) < 2:
        print("usage: python3 compiler.py program.json", file=sys.stderr)
        return 1
    with open(sys.argv[1], encoding="utf-8") as f:
        ast = json.load(f)

    try:
        code = Compiler().stmt(ast)
    except LanguageError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 1

    print(json.dumps(code, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
