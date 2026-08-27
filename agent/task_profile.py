from __future__ import annotations

import re
from dataclasses import dataclass


QuestionMode = str


@dataclass(frozen=True)
class TaskProfile:
    """Conservative, model-free description of the requested answer shape."""

    mode: QuestionMode
    confidence: float
    alternate_modes: tuple[QuestionMode, ...]
    part_count: int
    blank_count: int
    choice_count: int | None
    requires_proof: bool
    requires_all_solutions: bool
    obligations: tuple[str, ...]
    ambiguity_flags: tuple[str, ...]


_PROOF_MARKERS = (
    "证明",
    "严格证明",
    "严格说明",
    "给出证明",
    "prove that",
    "show that",
    "justify rigorously",
)

_DERIVATION_MARKERS = (
    "严格推导",
    "推导",
    "说明为什么",
    "解释为什么",
    "说明理由",
    "给出理由",
    "验证其关系",
    "验证关系",
    "并验证",
    "derive",
    "explain why",
    "justify",
    "verify",
)

_ALL_SOLUTION_MARKERS = (
    "所有解",
    "全部解",
    "解集",
    "所有可能",
    "all solutions",
    "all possible",
    "determine all",
    "find all",
)

_CALCULATION_MARKERS = (
    "求",
    "计算",
    "数值",
    "find",
    "compute",
    "evaluate",
    "determine",
)


def _flatten(text: str) -> str:
    return " ".join(text.strip().split()).lower()


def _part_labels(problem: str) -> tuple[str, ...]:
    problem = problem.replace("\\n", "\n")
    patterns = (
        r"(?m)^\s*[（(]\s*(\d+|[一二三四五六七八九十]+)\s*[)）]",
        r"(?m)^\s*([a-zA-Z])\s*[.)、]",
        r"[①②③④⑤⑥⑦⑧⑨⑩]",
    )
    labels: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, problem):
            value = match.group(1) if match.lastindex else match.group(0)
            if value not in labels:
                labels.append(value)
    if re.search(r"要求|分别|完成下列", problem):
        for match in re.finditer(r"[（(]\s*(\d+|[一二三四五六七八九十]+)\s*[)）]", problem):
            value = match.group(1)
            if value not in labels:
                labels.append(value)
    return tuple(labels)


def _option_labels(problem: str) -> tuple[str, ...]:
    """Detect common inline and line-separated A-F option labels."""

    problem = problem.replace("\\n", "\n")
    pattern = re.compile(
        r"(?:^|[\s；;])\s*[（(]?\s*([A-FＡ-Ｆ])\s*(?:[)）]|[.、:：])\s*",
        flags=re.MULTILINE,
    )
    labels: list[str] = []
    for match in pattern.finditer(problem):
        value = match.group(1).upper()
        value = chr(ord("A") + ord(value) - ord("Ａ")) if "Ａ" <= value <= "Ｆ" else value
        if value not in labels:
            labels.append(value)
    return tuple(labels)


def _blank_count(problem: str) -> int:
    spans: list[tuple[int, int]] = []
    patterns = (
        r"_{2,}|＿{2,}",
        r"\\(?:blank|underline)\s*(?:\{[^{}]*\})?",
        r"[（(]\s*(?:空|填空)?\s*[)）]",
    )
    for pattern in patterns:
        spans.extend(match.span() for match in re.finditer(pattern, problem, flags=re.IGNORECASE))
    spans.sort()
    distinct: list[tuple[int, int]] = []
    for span in spans:
        if not distinct or span[0] >= distinct[-1][1]:
            distinct.append(span)
    return len(distinct)


def _explicit_choice_count(text: str) -> int | None:
    word_numbers = {
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
    }
    match = re.search(
        r"(?:选择|选出|pick|choose|select)\s*(?:其中|the)?\s*"
        r"([1-5一二两三四五]|one|two|three|four|five)\s*"
        r"(?:个|项|answers?|options?)",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        token = match.group(1).lower()
        return int(token) if token.isdigit() else word_numbers.get(token)
    if re.search(r"单选|唯一正确|恰有一个|exactly one|single[- ]choice", text, flags=re.IGNORECASE):
        return 1
    return None


def _score_modes(problem: str) -> tuple[dict[str, float], int, int, int | None, bool, bool, bool]:
    lowered = _flatten(problem)
    options = _option_labels(problem)
    parts = _part_labels(problem)
    blanks = _blank_count(problem)
    requires_proof = any(marker in lowered for marker in _PROOF_MARKERS)
    requires_derivation = any(marker in lowered for marker in _DERIVATION_MARKERS)
    requires_all = any(marker in lowered for marker in _ALL_SOLUTION_MARKERS)

    scores = {
        "open_response": 0.15,
        "calculation": 0.0,
        "proof": 0.0,
        "choice": 0.0,
        "fill": 0.0,
        "true_false": 0.0,
        "multipart": 0.0,
        "solve_all": 0.0,
    }
    if any(marker in lowered for marker in _CALCULATION_MARKERS):
        scores["calculation"] += 0.68
    if requires_proof:
        scores["proof"] += 0.9
    if requires_all:
        scores["solve_all"] += 0.82
    if len(options) >= 2:
        scores["choice"] += 0.72 + min(0.18, 0.04 * len(options))
    if re.search(r"选择题|多选|单选|正确选项|incorrect option|which of the following", lowered):
        scores["choice"] += 0.25
    if blanks:
        scores["fill"] += 0.78 + min(0.16, 0.04 * blanks)
    if re.search(r"填空|fill in the blank", lowered):
        scores["fill"] += 0.24
    if re.search(
        r"判断(?:下列|命题|说法)?.{0,12}(?:正误|真假|正确|错误)|true or false",
        lowered,
    ):
        scores["true_false"] += 0.86
    if len(parts) >= 2:
        scores["multipart"] += 0.82 + min(0.14, 0.03 * len(parts))

    return (
        scores,
        max(1, len(parts)),
        blanks,
        _explicit_choice_count(lowered),
        requires_proof,
        requires_derivation,
        requires_all,
    )


def analyze_task(problem: str) -> TaskProfile:
    (
        scores,
        part_count,
        blanks,
        choice_count,
        requires_proof,
        requires_derivation,
        requires_all,
    ) = _score_modes(problem)
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best_mode, best_score = ranked[0]
    second_mode, second_score = ranked[1]

    ambiguity: list[str] = []
    if best_score < 0.62:
        best_mode = "open_response"
        ambiguity.append("weak_mode_signal")
    if best_score - second_score < 0.16 and second_score >= 0.45:
        ambiguity.append("overlapping_mode_signals")
    if requires_proof and part_count > 1:
        ambiguity.append("multipart_proof")

    confidence = max(0.35, min(0.99, best_score))
    alternates = tuple(mode for mode, score in ranked if mode != best_mode and score >= 0.35)[:2]

    obligations: list[str] = []
    if best_mode == "choice":
        obligations.append("choice_letters")
        if choice_count is not None:
            obligations.append(f"choice_count:{choice_count}")
    if best_mode == "fill" and blanks:
        obligations.append(f"blank_count:{blanks}")
    if best_mode == "true_false":
        obligations.append("binary_verdict")
    if part_count > 1:
        obligations.append(f"multipart_count:{part_count}")
    if requires_proof:
        obligations.append("proof_chain")
    elif requires_derivation:
        obligations.append("derivation_chain")
    if requires_all:
        obligations.append("all_solutions")
    if not obligations:
        obligations.append("explicit_final_answer")

    return TaskProfile(
        mode=best_mode,
        confidence=round(confidence, 2),
        alternate_modes=alternates,
        part_count=part_count,
        blank_count=blanks,
        choice_count=choice_count,
        requires_proof=requires_proof,
        requires_all_solutions=requires_all,
        obligations=tuple(obligations),
        ambiguity_flags=tuple(ambiguity),
    )


def normalized_choice_letters(value: str) -> tuple[str, ...]:
    text = value.upper()
    text = "".join(
        chr(ord("A") + ord(char) - ord("Ａ")) if "Ａ" <= char <= "Ｆ" else char
        for char in text
    )
    letters = re.findall(r"(?<![A-Z])[A-F](?![A-Z])", text)
    if not letters and re.fullmatch(r"[A-F]{1,6}", re.sub(r"\s+", "", text)):
        letters = list(re.sub(r"\s+", "", text))
    return tuple(dict.fromkeys(letters))
