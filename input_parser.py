import re

from values import LanguageError, Sexp, String

INPUT_TOKEN_RE = re.compile(r'''\s*(\[|\]|\{|\}|\(|\)|[,;:]|-?[0-9]+|"[^"]*"|'[^']'|[A-Z][a-zA-Z_'0-9]*)''')

def parse_input(text):
    text = text.strip()
    tokens = []
    pos = 0
    while pos < len(text):
        m = INPUT_TOKEN_RE.match(text, pos)
        if not m:
            raise LanguageError(f"bad input at position {pos}")
        tokens.append(m.group(1))
        pos = m.end()
    values = []
    rest = read_values(tokens, values)
    if rest:
        raise LanguageError(f"unexpected {rest[0]!r} in input")
    return values

def read_values(tokens, values, end="]"):
    while tokens and tokens[0] != end:
        if values and tokens[0] in (",", ";"):
            tokens = tokens[1:]
        value, tokens = read_value(tokens)
        values.append(value)
    return tokens

def read_value(tokens):
    value, tokens = read_primary(tokens)
    if tokens and tokens[0] == ":":
        tail, tokens = read_value(tokens[1:])
        value = Sexp("cons", [value, tail])
    return value, tokens


def read_primary(tokens):
    if not tokens:
        raise LanguageError("unexpected end of input")
    token, tokens = tokens[0], tokens[1:]
    if token in ("[", "{"):
        end = "]" if token == "[" else "}"
        items = []
        tokens = read_values(tokens, items, end)
        if not tokens:
            kind = "array" if token == "[" else "list"
            raise LanguageError(f"unterminated {kind} in input")
        if token == "{":
            value = Sexp("nil", [])
            for item in reversed(items):
                value = Sexp("cons", [item, value])
            return value, tokens[1:]
        return items, tokens[1:]
    if token.startswith('"'):
        return String(map(ord, token[1:-1])), tokens
    if token.startswith("'"):
        return ord(token[1]), tokens
    if token[0].isupper():
        args = []
        if tokens and tokens[0] == "(":
            tokens = read_values(tokens[1:], args, ")")
            if not tokens:
                raise LanguageError("unterminated constructor in input")
            tokens = tokens[1:]
        return Sexp(token, args), tokens
    if token == "(":
        value, tokens = read_value(tokens)
        if not tokens or tokens[0] != ")":
            raise LanguageError("unterminated parentheses in input")
        return value, tokens[1:]
    if token in ("]", "}", ")", ",", ";", ":"):
        raise LanguageError(f"unexpected {token!r} in input")
    return int(token), tokens

