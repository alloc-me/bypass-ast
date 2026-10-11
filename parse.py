import re


class ParseError(Exception):
    pass


KEYWORDS = {"read", "write", "skip", "while", "do", "for", "if", "else", "elif"}

OPERATORS = ["!!", "&&", "==", "!=", "<=", ">=", "<", ">", "+", "-", "*", "/", "%", "="]
PUNCT = "(){};"

CONST_RE = re.compile(r"[0-9]+")
IDENT_RE = re.compile(r"[a-z][a-zA-Z_'0-9]*")

BINOP_LEVELS = [
    ["!!"],
    ["&&"],
    ["==", "!=", "<=", "<", ">=", ">"],
    ["+", "-"],
    ["*", "/", "%"],
]


def tokenize(text):
    tokens = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text.startswith("--", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end + 1
        elif text.startswith("(*", i):
            end = text.find("*)", i + 2)
            if end < 0:
                raise ParseError("unterminated comment (*")
            i = end + 2
        elif m := CONST_RE.match(text, i):
            tokens.append(("const", int(m.group())))
            i = m.end()
        elif m := IDENT_RE.match(text, i):
            word = m.group()
            tokens.append(("keyword" if word in KEYWORDS else "ident", word))
            i = m.end()
        elif text[i] in PUNCT:
            tokens.append((text[i], text[i]))
            i += 1
        else:
            for op in OPERATORS:
                if text.startswith(op, i):
                    tokens.append(("op", op))
                    i += len(op)
                    break
            else:
                raise ParseError(f"unexpected character {text[i]!r} at position {i}")
    tokens.append(("eof", None))
    return tokens


def seq(stmts):
    node = stmts[-1]
    for stmt in reversed(stmts[:-1]):
        node = {"seq": {"left": stmt, "right": node}}
    return node


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        return self.tokens[self.pos + offset]

    def at(self, kind, value=None):
        k, v = self.peek()
        return k == kind and (value is None or v == value)

    def accept(self, kind, value=None):
        if self.at(kind, value):
            tok = self.peek()
            self.pos += 1
            return tok
        return None

    def expect(self, kind, value=None):
        tok = self.accept(kind, value)
        if tok is None:
            got = self.peek()[1]
            raise ParseError(f"{value or kind!r} expected, got {got or 'end of program'!r}")
        return tok

    def parse_program(self):
        self.expect("{")
        body = self.parse_block()
        self.expect("}")
        if not self.at("eof"):
            raise ParseError(f"unexpected {self.peek()[1]!r} after program")
        return body

    def parse_block(self):
        stmts = []
        while not self.at("}") and not self.at("eof"):
            stmts.append(self.parse_stmt())
            self.accept(";")
        if not stmts:
            raise ParseError("at least one statement expected")
        return seq(stmts)

    def parse_stmt(self):
        if self.accept("{"):
            body = self.parse_block()
            self.expect("}")
            return body

        if self.at("keyword"):
            return self.parse_keyword_stmt(self.peek()[1])

        name = self.expect("ident")[1]
        if self.accept("op", "="):
            return {"assn": {"dst": name, "src": self.parse_expr()}}
        if self.at("op") and self.peek(1) == ("op", "="):
            op = self.peek()[1]
            self.pos += 2
            src = {"binop": op, "left": {"var": name}, "right": self.parse_expr()}
            return {"assn": {"dst": name, "src": src}}
        raise ParseError(f"'=' expected after {name!r}")

    def parse_keyword_stmt(self, word):
        self.pos += 1

        if word == "skip":
            return "skip"

        if word == "read":
            self.expect("(")
            name = self.expect("ident")[1]
            self.expect(")")
            return {"read": name}

        if word == "write":
            self.expect("(")
            expr = self.parse_expr()
            self.expect(")")
            return {"write": expr}

        if word == "while":
            cond = self.parse_paren_expr()
            return {"while": {"cond": cond, "body": self.parse_stmt()}}

        if word == "do":
            body = self.parse_stmt()
            self.accept(";")
            self.expect("keyword", "while")
            return {"do": {"body": body, "cond": self.parse_paren_expr()}}

        if word == "for":
            self.expect("(")
            init = self.parse_stmt()
            self.accept(";")
            cond = self.parse_expr()
            self.expect(";")
            step = self.parse_stmt()
            self.expect(")")
            body = self.parse_stmt()
            return seq([init, {"while": {"cond": cond, "body": seq([body, step])}}])

        if word == "if":
            cond = self.parse_paren_expr()
            then = self.parse_stmt()
            return {"if": {"cond": cond, "then": then, "else": self.parse_else()}}

        raise ParseError(f"unexpected keyword {word!r}")

    def parse_else(self):
        if self.at(";") and self.peek(1)[0] == "keyword" and self.peek(1)[1] in ("else", "elif"):
            self.pos += 1
        if self.accept("keyword", "else"):
            return self.parse_stmt()
        if self.accept("keyword", "elif"):
            cond = self.parse_paren_expr()
            then = self.parse_stmt()
            return {"if": {"cond": cond, "then": then, "else": self.parse_else()}}
        return "skip"

    def parse_paren_expr(self):
        self.expect("(")
        expr = self.parse_expr()
        self.expect(")")
        return expr

    def parse_expr(self, level=0):
        if level == len(BINOP_LEVELS):
            return self.parse_primary()
        node = self.parse_expr(level + 1)
        while self.at("op") and self.peek()[1] in BINOP_LEVELS[level]:
            op = self.peek()[1]
            self.pos += 1
            node = {"binop": op, "left": node, "right": self.parse_expr(level + 1)}
        return node

    def parse_primary(self):
        if self.at("const"):
            return {"const": self.accept("const")[1]}
        if self.at("ident"):
            return {"var": self.accept("ident")[1]}
        if self.accept("("):
            expr = self.parse_expr()
            self.expect(")")
            return expr
        raise ParseError(f"expression expected, got {self.peek()[1] or 'end of program'!r}")
