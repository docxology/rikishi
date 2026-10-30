from __future__ import annotations

import re
from dataclasses import dataclass, replace

from rikishi.inference_models import InferenceError
from rikishi.kif import Expression, parse

_SYMBOL = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")
_VARIABLE = re.compile(r"\?[A-Za-z][A-Za-z0-9_-]*\Z")
_NUMBER = re.compile(r"[0-9]+\Z")


def _name(prefix: str, value: str) -> str:
    return prefix + value.encode().hex()


@dataclass(frozen=True)
class _Scope:
    substitutions: dict[str, str]
    used: set[str]
    free: set[str]
    bound: frozenset[str] = frozenset()


class Compiler:
    """Share one arity table across a problem; symbols-as-objects remain distinct."""

    def __init__(self) -> None:
        self.arities: dict[str, int] = {}

    def formula(self, text: str, bindings: dict[str, str] | None = None) -> str:
        """Close free variables universally, after finite predicate specialization."""
        formulas = list(parse(text))
        if len(formulas) != 1:
            raise InferenceError("Exactly one complete formula is required")
        substitutions = bindings or {}
        if any(not _VARIABLE.fullmatch(k) or not _SYMBOL.fullmatch(v)
               for k, v in substitutions.items()):
            raise InferenceError("Predicate specializations require variable-to-symbol bindings")
        scope = _Scope(substitutions, set(), set())
        result = self._formula(formulas[0].expression, scope)
        if scope.used != substitutions.keys():
            raise InferenceError("Unused predicate specialization")
        if scope.free:
            result = f"(![{','.join(_name('V', v) for v in sorted(scope.free))}]:{result})"
        return result

    def _term(self, value: Expression, scope: _Scope) -> str:
        if not isinstance(value, str):
            raise InferenceError("Function terms and strings are outside the supported fragment")
        if value in scope.substitutions:
            scope.used.add(value)
            value = scope.substitutions[value]
        if _VARIABLE.fullmatch(value):
            if value not in scope.bound:
                scope.free.add(value)
            return _name("V", value)
        if _SYMBOL.fullmatch(value) or _NUMBER.fullmatch(value):
            return _name("c_", value)
        raise InferenceError(f"Unsupported term: {value}")

    def _formula(self, expression: Expression, scope: _Scope) -> str:
        if not isinstance(expression, tuple):
            raise InferenceError("A formula requires a fixed predicate or logical operator")
        head = expression[0]
        if not isinstance(head, str):
            raise InferenceError("A formula requires a fixed predicate or logical operator")
        args = expression[1:]
        if head in {"forall", "exists"}:
            if (len(args) != 2 or not isinstance(args[0], tuple) or not args[0]
                    or any(not isinstance(v, str) or not _VARIABLE.fullmatch(v) for v in args[0])):
                raise InferenceError("A quantifier requires distinct variables and one body")
            variables = tuple(str(v) for v in args[0])
            if len(set(variables)) != len(variables) or set(variables) & scope.substitutions.keys():
                raise InferenceError("Duplicate or specialized quantified variable")
            body = self._formula(args[1], replace(scope, bound=scope.bound | frozenset(variables)))
            quantifier = "!" if head == "forall" else "?"
            return f"({quantifier}[{','.join(_name('V', v) for v in variables)}]:{body})"
        if head in {"and", "or", "=>", "<=>", "not"}:
            required = 1 if head == "not" else 2
            if len(args) < required or (head in {"not", "=>", "<=>"} and len(args) != required):
                raise InferenceError("Invalid logical operator arity")
            parts = [self._formula(a, scope) for a in args]
            if head == "not":
                return f"~({parts[0]})"
            operator = {"and": " & ", "or": " | ", "=>": " => ", "<=>": " <=> "}[head]
            return "(" + operator.join(parts) + ")"
        if head == "equal":
            if len(args) != 2:
                raise InferenceError("Equality requires exactly two terms")
            terms = [self._term(a, scope) for a in args]
            return f"({terms[0]} = {terms[1]})"
        if head in scope.substitutions:
            scope.used.add(head)
            head = scope.substitutions[head]
        if not _SYMBOL.fullmatch(head) or not args:
            raise InferenceError("Predicate variables, row variables and nullary atoms are unsupported")
        if head in self.arities and self.arities[head] != len(args):
            raise InferenceError(f"Inconsistent predicate arity: {head}")
        self.arities[head] = len(args)
        terms = [self._term(a, scope) for a in args]
        return f"{_name('r_', head)}({','.join(terms)})"
