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
        if "sexp" in expression:
            code = []
            for item in expression["args"]:
                code += self.expr(item)
            return code + [{"SEXP": [expression["sexp"], len(expression["args"])]}]
        if "elem" in expression:
            return self.expr(expression["elem"]) + self.expr(expression["index"]) + ["ELEM"]
        if "length" in expression:
            return self.expr(expression["length"]) + ["LENGTH"]
        return self.expr(expression["left"]) + self.expr(expression["right"]) + [{"BINOP": expression["binop"]}]

    def pattern_failure(self, depth, failures, next_branch):
        if depth == 0:
            return next_branch
        if depth not in failures:
            failures[depth] = self.label("pattern_drop")
        return failures[depth]

    def pattern(self, pattern, failures, next_branch, depth=1):
        if isinstance(pattern, int):
            fail = self.pattern_failure(depth - 1, failures, next_branch)
            return [{"CONST": pattern}, {"BINOP": "=="}, {"JZ": fail}]
        if isinstance(pattern, str):
            if pattern in ("#int", "#array", "#string", "#sexp"):
                fail = self.pattern_failure(depth - 1, failures, next_branch)
                return [{"PATT": pattern}, {"JZ": fail}]
            type_fail = self.pattern_failure(depth, failures, next_branch)
            value_fail = self.pattern_failure(depth - 1, failures, next_branch)
            return ["DUP", {"PATT": "#string"}, {"JZ": type_fail},
                    {"STRING": pattern}, {"BINOP": "=="}, {"JZ": value_fail}]
        if not isinstance(pattern, dict):
            raise CompilerError(f"unknown pattern: {pattern!r}")
        if "wildcard" in pattern:
            return ["DROP"]
        if "bind" in pattern:
            return self.pattern(pattern["bind"]["pattern"], failures, next_branch, depth)
        fail = self.pattern_failure(depth, failures, next_branch)
        if "array" in pattern:
            parts = pattern["array"]
            code = ["DUP", {"PATT": "#array"}, {"JZ": fail},
                    "DUP", "LENGTH", {"CONST": len(parts)}, {"BINOP": "=="}, {"JZ": fail}]
        elif "sexp" in pattern:
            parts = pattern["args"]
            code = ["DUP", {"PATT": ["Tag", pattern["sexp"], len(parts)]}, {"JZ": fail}]
        else:
            raise CompilerError(f"unknown pattern: {pattern!r}")
        for index, part in enumerate(parts):
            code += ["DUP", {"CONST": index}, "ELEM"]
            code += self.pattern(part, failures, next_branch, depth + 1)
        return code + ["DROP"]

    def pattern_bindings(self, pattern, path=()):
        if not isinstance(pattern, dict):
            return []
        if "bind" in pattern:
            binding = pattern["bind"]
            code = self.pattern_bindings(binding["pattern"], path)
            code += [{"LD": "_"}]
            for index in path:
                code += [{"CONST": index}, "ELEM"]
            return code + [{"ST": binding["name"]}]
        if "array" in pattern:
            parts = pattern["array"]
        elif "sexp" in pattern:
            parts = pattern["args"]
        else:
            return []
        code = []
        for index, part in enumerate(parts):
            code += self.pattern_bindings(part, path + (index,))
        return code

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

        if kind == "switch":
            end = self.label("switch_end")
            code = self.expr(arg["scrutinee"])
            for branch in arg["branches"]:
                next_branch = self.label("next_pattern")
                failures = {}
                code += ["DUP"] + self.pattern(branch["pattern"], failures, next_branch)
                code += ["SCOPE", {"ST": "_"}]
                code += self.pattern_bindings(branch["pattern"])
                code += ["ENTER"] + self.stmt(branch["branch"])
                code += ["LEAVE", {"JMP": end}]
                for depth, label in failures.items():
                    code += [{"LABEL": label}] + ["DROP"] * depth + [{"JMP": next_branch}]
                code += [{"LABEL": next_branch}]
            return code + ["MF", {"LABEL": end}]

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
