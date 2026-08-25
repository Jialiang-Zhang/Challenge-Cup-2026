from __future__ import annotations

import math
import re
from fractions import Fraction
from typing import Any

from .models import EquivalenceStatus

try:  # SymPy is optional at import time; tools degrade to UNKNOWN without it.
    import sympy as sp
except Exception:  # pragma: no cover - exercised when dependency is absent.
    sp = None  # type: ignore[assignment]


PREFIX_RE = re.compile(
    r"^(?:final[_ ]candidate|final answer|answer|最终答案|答案)\s*[:：]\s*",
    flags=re.IGNORECASE,
)


def _extract_balanced_command(text: str, command: str) -> str:
    pattern = re.compile(rf"\\{re.escape(command)}\s*\{{")
    matches = list(pattern.finditer(text))
    if not matches:
        return text
    match = matches[-1]
    brace_start = text.find("{", match.start())
    depth = 0
    for index in range(brace_start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start + 1 : index]
    return text


def _replace_simple_latex_fractions(text: str) -> str:
    previous = None
    current = text
    pattern = re.compile(r"\\(?:d?frac)\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
    while previous != current:
        previous = current
        current = pattern.sub(r"((\1)/(\2))", current)
    return current


def _replace_simple_sqrt(text: str) -> str:
    return re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", text)


def normalize_answer_text(value: str) -> str:
    text = value.strip()
    if not text:
        return ""

    if "\\boxed" in text:
        text = _extract_balanced_command(text, "boxed")

    text = PREFIX_RE.sub("", text.strip())
    text = text.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\\left", "").replace("\\right", "")
    text = text.replace("\\displaystyle", "")
    text = text.replace("\\,", "").replace("\\;", "").replace("\\!", "")
    text = text.replace("\\pi", "pi").replace("π", "pi")
    text = text.replace("\\infty", "oo").replace("∞", "oo")
    text = text.replace("\\cdot", "*").replace("\\times", "*")
    text = text.replace("\\pm", "+-")
    text = _replace_simple_latex_fractions(text)
    text = _replace_simple_sqrt(text)
    text = text.replace("$", "")
    text = re.sub(r"\\text\s*\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\s+", "", text)
    text = text.strip("。.;；,，")
    text = re.sub(
        r"[（(](?:个|种|棵|项|元|个元素|ways?|solutions?)[)）]$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _try_fraction(value: str) -> Fraction | None:
    normalized = normalize_answer_text(value)
    if not normalized or len(normalized) > 128:
        return None
    if re.fullmatch(r"[+-]?\d+", normalized):
        return Fraction(int(normalized), 1)
    if re.fullmatch(r"[+-]?\d+/[+-]?\d+", normalized):
        numerator, denominator = normalized.split("/", 1)
        if int(denominator) == 0:
            return None
        return Fraction(int(numerator), int(denominator))
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\d*\.\d+)", normalized):
        return Fraction(normalized)
    wrapped = re.fullmatch(
        r"([+-]?)\(\(([+-]?\d+)\)/\(([+-]?\d+)\)\)\)",
        normalized,
    )
    if wrapped and int(wrapped.group(3)) != 0:
        sign = -1 if wrapped.group(1) == "-" else 1
        return Fraction(sign * int(wrapped.group(2)), int(wrapped.group(3)))
    return None


def _try_unique_embedded_fraction(value: str) -> Fraction | None:
    direct = _try_fraction(value)
    if direct is not None:
        return direct
    text = value.replace("$", "")
    # Do not mistake exponents or coefficients inside a genuine symbolic
    # expression for the answer itself. Embedded extraction is only a fallback
    # for prose such as "the answer is -1".
    if re.search(r"[A-Za-z_]+\s*\(", text) or any(
        op in text for op in ("^", "**", "=")
    ):
        return None
    latex_tokens = re.findall(
        r"[+-]?\\(?:d?frac)\s*\{[+-]?\d+\}\s*\{[+-]?\d+\}", text
    )
    plain_tokens = re.findall(
        r"(?<![A-Za-z0-9_])[+-]?\d+(?:/\d+|\.\d+)?(?![A-Za-z0-9_])",
        text,
    )
    tokens = latex_tokens + plain_tokens
    parsed = [
        fraction
        for token in tokens
        if (fraction := _try_fraction(token)) is not None
    ]
    unique = set(parsed)
    return next(iter(unique)) if len(unique) == 1 else None


def _safe_sympy_expression(value: str) -> Any | None:
    if sp is None:
        return None
    normalized = normalize_answer_text(value)
    if not normalized or len(normalized) > 512:
        return None
    if any(token in normalized for token in ("__", "'", '"', "`", ":", ";")):
        return None
    if re.search(r"\b(?:import|exec|eval|open|globals|locals|lambda)\b", normalized):
        return None
    if any(token in normalized for token in ("=", "<", ">")):
        return None
    if not re.fullmatch(r"[A-Za-z0-9_+\-*/^().,]+", normalized):
        return None

    normalized = normalized.replace("^", "**")
    identifiers = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", normalized))
    allowed_functions: dict[str, Any] = {
        "sqrt": sp.sqrt,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "exp": sp.exp,
        "log": sp.log,
        "Abs": sp.Abs,
        "pi": sp.pi,
        "E": sp.E,
        "I": sp.I,
        "oo": sp.oo,
    }
    local_dict: dict[str, Any] = dict(allowed_functions)
    for identifier in identifiers:
        if identifier not in local_dict:
            local_dict[identifier] = sp.Symbol(identifier)
    try:
        return sp.sympify(normalized, locals=local_dict, evaluate=True)
    except Exception:
        return None


def _parse_finite_set(value: str) -> tuple[str, ...] | None:
    normalized = normalize_answer_text(value)
    if normalized.startswith("\\{") and normalized.endswith("\\}"):
        normalized = normalized[2:-2]
    elif normalized.startswith("{") and normalized.endswith("}"):
        normalized = normalized[1:-1]
    else:
        return None
    if not normalized:
        return ()
    if any(token in normalized for token in (":", "|", "<", ">")):
        return None
    parts = [part for part in normalized.split(",") if part]
    if not parts:
        return None
    canonical_parts: list[str] = []
    for part in parts:
        fraction = _try_fraction(part)
        if fraction is not None:
            canonical_parts.append(f"{fraction.numerator}/{fraction.denominator}")
        else:
            canonical_parts.append(part)
    return tuple(sorted(set(canonical_parts)))


def compare_answers(a: str, b: str) -> EquivalenceStatus:
    normalized_a = normalize_answer_text(a)
    normalized_b = normalize_answer_text(b)
    if not normalized_a or not normalized_b:
        return "unknown"
    if normalized_a.casefold() == normalized_b.casefold():
        return "equivalent"

    fraction_a = _try_unique_embedded_fraction(a)
    fraction_b = _try_unique_embedded_fraction(b)
    if fraction_a is not None and fraction_b is not None:
        return "equivalent" if fraction_a == fraction_b else "not_equivalent"

    set_a = _parse_finite_set(a)
    set_b = _parse_finite_set(b)
    if set_a is not None and set_b is not None:
        return "equivalent" if set_a == set_b else "not_equivalent"

    expr_a = _safe_sympy_expression(a)
    expr_b = _safe_sympy_expression(b)
    if expr_a is not None and expr_b is not None:
        try:
            difference = sp.simplify(expr_a - expr_b)
            if difference == 0:
                return "equivalent"
            if difference.is_number:
                numeric = complex(sp.N(difference, 30))
                if math.isfinite(numeric.real) and math.isfinite(numeric.imag):
                    return "not_equivalent"
        except Exception:
            return "unknown"

    return "unknown"


def numeric_value(value: str) -> float | None:
    fraction = _try_fraction(value)
    if fraction is not None:
        return float(fraction)
    expr = _safe_sympy_expression(value)
    if expr is not None and getattr(expr, "is_number", False):
        try:
            numeric = complex(sp.N(expr, 30))
            if abs(numeric.imag) < 1e-12 and math.isfinite(numeric.real):
                return float(numeric.real)
        except Exception:
            return None
    return None


def answer_appears_in_response(answer: str, response: str) -> bool:
    normalized_answer = normalize_answer_text(answer)
    normalized_response = normalize_answer_text(response)
    if not normalized_answer or not normalized_response:
        return False
    if normalized_answer.casefold() in normalized_response.casefold():
        return True
    answer_fraction = _try_fraction(answer)
    if answer_fraction is None:
        return False
    for fragment in re.findall(r"[+-]?\d+(?:/\d+|\.\d+)?", response):
        fragment_fraction = _try_fraction(fragment)
        if fragment_fraction == answer_fraction:
            return True
    return False
