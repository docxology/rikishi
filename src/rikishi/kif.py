from collections.abc import Iterator
from dataclasses import dataclass


class KifError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class String:
    value: str


type Expression = str | String | tuple[Expression, ...]


@dataclass(frozen=True, slots=True)
class Formula:
    expression: tuple[Expression, ...]
    text: str
    line: int


def parse(text: str, source: str = "<input>") -> Iterator[Formula]:
    stack: list[list[Expression]] = []
    start = 0
    start_line = 1
    line = 1
    position = 0
    while position < len(text):
        char = text[position]
        if char.isspace():
            line += char == "\n"
            position += 1
        elif char == ";":
            end = text.find("\n", position)
            position = end if end >= 0 else len(text)
        elif char == "(":
            if not stack:
                start, start_line = position, line
            stack.append([])
            position += 1
        elif char == ")":
            if not stack:
                raise KifError(f"{source}:{line}: unmatched closing parenthesis")
            expression = tuple(stack.pop())
            if not expression:
                raise KifError(f"{source}:{line}: empty expression")
            position += 1
            if stack:
                stack[-1].append(expression)
            else:
                yield Formula(expression, text[start:position], start_line)
        elif char == '"':
            if not stack:
                raise KifError(f"{source}:{line}: string outside formula")
            position += 1
            characters: list[str] = []
            while position < len(text):
                char = text[position]
                if char == '"':
                    position += 1
                    break
                if char == "\\":
                    position += 1
                    if position == len(text):
                        raise KifError(f"{source}:{line}: unfinished string escape")
                    char = text[position]
                line += char == "\n"
                characters.append(char)
                position += 1
            else:
                raise KifError(f"{source}:{line}: unterminated string")
            stack[-1].append(String("".join(characters)))
        else:
            end = position
            while end < len(text) and not text[end].isspace() and text[end] not in '();"':
                end += 1
            atom = text[position:end]
            if not stack:
                raise KifError(f"{source}:{line}: atom outside formula: {atom[:60]}")
            stack[-1].append(atom)
            position = end
    if stack:
        raise KifError(f"{source}:{start_line}: unclosed formula")


def symbols(expression: Expression) -> set[str]:
    if isinstance(expression, tuple):
        result: set[str] = set()
        for child in expression:
            result.update(symbols(child))
        return result
    if isinstance(expression, String) or expression.startswith(("?", "@")):
        return set()
    if expression in {"and", "or", "not", "=>", "<=>", "forall", "exists", "equal"}:
        return set()
    try:
        float(expression)
    except ValueError:
        return {expression}
    return set()
