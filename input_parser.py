import re

from values import LanguageError, String

INPUT_TOKEN_RE = re.compile(r'\s*(\[|\]|[,;]|-?[0-9]+|"[^"]*")')

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

def read_values(tokens, values):
    while tokens and tokens[0] != "]":
        if values and tokens[0] in (",", ";"):
            tokens = tokens[1:]
        value, tokens = read_value(tokens)
        values.append(value)
    return tokens

def read_value(tokens):
    if not tokens:
        raise LanguageError("unexpected end of input")
    token, tokens = tokens[0], tokens[1:]
    if token == "[":
        items = []
        tokens = read_values(tokens, items)
        if not tokens:
            raise LanguageError("unterminated array in input")
        return items, tokens[1:]
    if token.startswith('"'):
        return String(map(ord, token[1:-1])), tokens
    if token in ("]", ",", ";"):
        raise LanguageError(f"unexpected {token!r} in input")
    return int(token), tokens

