from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RequirementCheck:
    code: str
    status: str
    hard_failure: bool
    detail: str


_REASONING_RE = re.compile(
    r"(?:because|since|therefore|hence|thus|by\s+|由|因为|由于|根据|所以|因此|故|从而|可得|说明|验证)",
    flags=re.IGNORECASE,
)


def _has(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def _strict_derivation_ok(text: str) -> bool:
    chinese = bool(re.search(r"[\u4e00-\u9fff]", text))
    minimum = 180 if chinese else 320
    equations = len(re.findall(r"=|\\le|\\ge|≤|≥|\\Rightarrow|\\implies", text))
    return len(text) >= minimum and len(_REASONING_RE.findall(text)) >= 2 and equations >= 2


def _conflicting_local_truncation_order(text: str) -> bool:
    """Detect an explicit first-order truncation claim inside a claimed second-order proof.

    This is deliberately narrow: it fires only when a line/equation actually labels the local
    truncation error as O(h), while the same response claims second order/O(h^2). Merely mentioning
    O(h) in an intermediate Taylor term is not enough.
    """

    first_order_claim = bool(
        re.search(
            r"(?:\\tau|τ|局部截断误差|local\s+truncation)[^\n。]{0,260}(?:=|为|is)\s*O\s*\(\s*h\s*\)(?!\s*\^)",
            text,
            flags=re.IGNORECASE,
        )
    )
    second_order_claim = bool(
        re.search(
            r"(?:二阶|second[- ]order|O\s*\(\s*h\s*\^\s*2\s*\))",
            text,
            flags=re.IGNORECASE,
        )
    )
    return first_order_claim and second_order_claim


def evaluate_explicit_requirement_coverage(
    response: str,
    requirements: tuple[str, ...],
) -> list[RequirementCheck]:
    """Conservative structural checks for requirements explicitly stated by the problem.

    These checks never attempt to prove arbitrary mathematics. They prevent a candidate from
    claiming completion while omitting a named method/requested object or while containing a
    directly machine-detectable contradiction in a required derivation.
    """

    text = str(response or "")
    checks: list[RequirementCheck] = []
    if not requirements:
        return checks

    strict_requested = any(
        _has(req, r"严格(?:证明|推导|说明)|prove|derive|justify rigorously")
        for req in requirements
    )
    if strict_requested:
        ok = _strict_derivation_ok(text)
        checks.append(
            RequirementCheck(
                code="strict_derivation",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail=f"chars={len(text)};reasoning={len(_REASONING_RE.findall(text))}",
            )
        )

    named_requirements = (
        (r"傅里叶|fourier", r"傅里叶|fourier", "fourier_method"),
        (r"矩阵树|matrix[- ]tree", r"矩阵树|matrix[- ]tree", "matrix_tree_method"),
        (r"markov|马尔可夫", r"markov|马尔可夫", "markov_method"),
        (r"反射原理|reflection principle", r"反射原理|reflection principle", "reflection_method"),
        (r"高斯积分|gaussian integral", r"高斯积分|gaussian integral|\\int", "gaussian_integration"),
        (r"jensen|凸性", r"jensen|凸性|cauchy|柯西", "convexity_step"),
        (r"局部截断误差|local truncation", r"局部截断误差|local truncation|\\tau", "local_truncation"),
        (r"零稳定|zero[- ]stabil", r"零稳定|zero[- ]stabil|根.*(?:1/3|\\frac\{1\}\{3\})", "zero_stability"),
        (r"a-稳定|a[- ]stabil", r"a-稳定|a[- ]stabil|左半平面|left half", "a_stability"),
        (r"根轨迹|边界轨迹|root locus|boundary locus", r"根轨迹|边界轨迹|root locus|boundary locus|z\s*\(.*theta", "boundary_locus"),
        (r"条件越多.*条件熵越小|conditioning reduces entropy", r"条件越多.*条件熵越小|条件.*熵.*(?:小|不增)|conditioning.*entropy", "conditional_entropy_monotonicity"),
    )
    for req_pattern, response_pattern, code in named_requirements:
        if any(_has(req, req_pattern) for req in requirements):
            ok = _has(text, response_pattern)
            checks.append(
                RequirementCheck(
                    code=code,
                    status="pass" if ok else "fail",
                    hard_failure=not ok,
                    detail="named_requirement_present" if ok else "named_requirement_missing",
                )
            )

    if any(_has(req, r"局部截断误差|local truncation") for req in requirements):
        conflict = _conflicting_local_truncation_order(text)
        checks.append(
            RequirementCheck(
                code="local_truncation_order_consistency",
                status="fail" if conflict else "pass",
                hard_failure=conflict,
                detail="explicit_Oh_vs_second_order_conflict" if conflict else "no_direct_order_conflict",
            )
        )

    if any(_has(req, r"密度|density") for req in requirements):
        ok = _has(text, r"密度|density|f[_\{].*\(.*t")
        checks.append(
            RequirementCheck(
                code="density_requested",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail="density_present" if ok else "density_missing",
            )
        )

    if any(_has(req, r"两个.*(?:生成)?自同构|two.*automorph") for req in requirements):
        mapping_count = len(re.findall(r"\\mapsto|↦|\bmapsto\b", text, flags=re.IGNORECASE))
        ok = mapping_count >= 2
        checks.append(
            RequirementCheck(
                code="two_automorphisms",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail=f"mapping_count={mapping_count}",
            )
        )

    if any(_has(req, r"验证.*关系|relations?") for req in requirements):
        relation_signals = len(
            re.findall(
                r"(?:\^\s*\{?\d+\}?\s*=|\^\d+\s*=|srs|tau.*sigma.*tau|\\tau.*\\sigma.*\\tau|\^{-1}|inverse)",
                text,
                flags=re.IGNORECASE,
            )
        )
        ok = relation_signals >= 2
        checks.append(
            RequirementCheck(
                code="generator_relations",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail=f"relation_signals={relation_signals}",
            )
        )

    if any(_has(req, r"唯一.*零特征值|零特征值.*常数向量") for req in requirements):
        zero_ok = _has(text, r"零特征值|zero eigenvalue|lambda[_\{].*=\s*0")
        constant_ok = _has(text, r"常数向量|constant vector|全1向量|\\mathbf\{1\}")
        ok = zero_ok and constant_ok
        checks.append(
            RequirementCheck(
                code="zero_eigenvector_explanation",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail=f"zero={zero_ok};constant={constant_ok}",
            )
        )

    if strict_requested and any(_has(req, r"高斯积分|gaussian integral") for req in requirements):
        integral = _has(text, r"\\int|∫")
        conditional = _has(text, r"B_t\s*=|条件|condition(?:ing|al)?")
        ok = integral and conditional
        checks.append(
            RequirementCheck(
                code="explicit_gaussian_derivation",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail=f"integral={integral};conditional={conditional}",
            )
        )

    return checks
