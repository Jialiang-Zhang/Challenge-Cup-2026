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
_REVISION_RE = re.compile(
    r"(?:更准确地|更直接地|但最简洁|我们改为|标准结论是|实际上我们只需|"
    r"more precisely|more directly|actually,? we only need|instead,? we use|the standard conclusion is)",
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


def _bdf2_signature(requirements_text: str) -> bool:
    return (
        _has(requirements_text, r"局部截断误差|local truncation")
        and _has(requirements_text, r"3\s*-\s*4e|3-4e")
        and _has(requirements_text, r"根轨迹|边界轨迹|root locus|boundary locus")
    )


def _last_zero_signature(requirements_text: str) -> bool:
    return (
        _has(requirements_text, r"g[_\{]?T|最后一次过零|last zero")
        and _has(requirements_text, r"Markov|马尔可夫")
        and _has(requirements_text, r"反射原理|reflection")
        and _has(requirements_text, r"高斯积分|Gaussian integral")
    )


def evaluate_explicit_requirement_coverage(
    response: str,
    requirements: tuple[str, ...],
) -> list[RequirementCheck]:
    """Conservative completion and consistency certificates for explicit task requirements.

    The checks are intentionally narrow. They never try to judge arbitrary prose proofs; they veto
    only omissions or directly recognizable contradictions in a named derivation requested by the
    problem.
    """

    text = str(response or "")
    checks: list[RequirementCheck] = []
    if not requirements:
        return checks

    requirement_text = "\n".join(str(item or "") for item in requirements)
    strict_requested = any(
        _has(req, r"严格(?:证明|推导|说明)|prove|derive|justify rigorously")
        for req in requirements
    )
    proof_requested = strict_requested or any(
        _has(req, r"证明|prove") for req in requirements
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

    if proof_requested:
        revisions = len(_REVISION_RE.findall(text))
        abandoned = revisions >= 3
        checks.append(
            RequirementCheck(
                code="clean_proof_chain",
                status="fail" if abandoned else "pass",
                hard_failure=abandoned,
                detail=f"revision_markers={revisions}",
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

    if _bdf2_signature(requirement_text):
        compact = re.sub(r"\s+", "", text)
        bad_coefficient = any(
            token in compact
            for token in (
                r"-\frac{h^3}{3}y'''",
                r"-\frac{h^2}{6}y'''",
                r"-\frac{h^3}{3}y^{(3)}",
                r"-\frac{h^2}{6}y^{(3)}",
            )
        )
        correct_coefficient = any(
            token in compact
            for token in (
                r"-\frac{2}{3}h^3y'''",
                r"-\frac{2h^3}{3}y'''",
                r"-\frac13h^2y'''",
                r"-\frac{1}{3}h^2y'''",
            )
        )
        checks.append(
            RequirementCheck(
                code="bdf2_taylor_coefficient",
                status="fail" if bad_coefficient else ("pass" if correct_coefficient else "unknown"),
                hard_failure=bad_coefficient,
                detail=(
                    "wrong_third_derivative_coefficient"
                    if bad_coefficient
                    else ("expected_coefficient_present" if correct_coefficient else "coefficient_not_parsed")
                ),
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

    if _last_zero_signature(requirement_text):
        compact = re.sub(r"\s+", "", text)
        nested_gaussian = compact.count(r"\int_{0}^{\infty}") >= 1 and compact.count(r"\int_{0}^{") >= 2
        doubled_prefactor = nested_gaussian and r"\frac{4}{\pi}" in compact
        checks.append(
            RequirementCheck(
                code="brownian_last_zero_gaussian_normalization",
                status="fail" if doubled_prefactor else "pass",
                hard_failure=doubled_prefactor,
                detail=(
                    "double_integral_prefactor_doubled"
                    if doubled_prefactor
                    else "no_detected_gaussian_prefactor_conflict"
                ),
            )
        )

    return checks
