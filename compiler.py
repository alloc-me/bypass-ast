import json
import sys

from parse import ParseError, Parser, tokenize


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

        raise ParseError(f"unknown statement {kind!r}")


def main():
    if len(sys.argv) < 2:
        print("usage: python3 compiler.py program.txt [--sm]", file=sys.stderr)
        return 1
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()

    try:
        ast = Parser(tokenize(text)).parse_program()
    except ParseError as ex:
        print(f"Input error: {ex}", file=sys.stderr)
        return 1

    result = Compiler().stmt(ast) if "--sm" in sys.argv[2:] else ast
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
