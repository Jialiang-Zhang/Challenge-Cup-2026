from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CrossDomainCertificate:
    code: str
    status: str
    hard_failure: bool
    detail: str


def _has(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, str(text or ""), flags=re.IGNORECASE | re.DOTALL))


def evaluate_cross_domain_certificates(*, answer_raw: str, response: str) -> list[CrossDomainCertificate]:
    """Catch local algebra/theorem-precondition contradictions visible in a submitted derivation.

    These checks inspect only the candidate itself. They do not use benchmark answers.
    """

    answer = str(answer_raw or "").strip()
    text = str(response or "")
    checks: list[CrossDomainCertificate] = []

    # A proof conclusion ending with a bare connective is not self-contained.
    dangling_has = bool(answer and re.search(r"(?:则.{0,100})?有\s*$", answer))
    if dangling_has:
        checks.append(
            CrossDomainCertificate(
                code="proof_conclusion_self_contained",
                status="fail",
                hard_failure=True,
                detail="candidate_ends_with_bare_has_cue",
            )
        )

    # Two-stage Radau IIA: the row sums of the displayed inverse and |R(iw)|^2
    # must be arithmetically compatible with the final rational function.
    radau = _has(text, r"Radau\s*IIA") or (
        _has(text, r"1\s*\+\s*\\frac\{1\}\{3\}\s*z")
        and _has(text, r"1\s*-\s*\\frac\{2\}\{3\}\s*z")
        and _has(text, r"\\frac\{1\}\{6\}\s*z\^2")
    )
    if radau:
        wrong_second_component = _has(
            text,
            r"Second component[^\n]{0,180}1\s*\+\s*\\frac\{1\}\{6\}\s*z|"
            r"第二分量[^\n]{0,180}1\s*\+\s*\\frac\{1\}\{6\}\s*z",
        )
        inconsistent_weighted_sum = _has(
            text,
            r"\\frac\{3\}\{4\}[^\n]{0,180}1-\\frac\{1\}\{3\}z[^\n]{0,180}"
            r"\\frac\{1\}\{4\}[^\n]{0,120}1\+\\frac\{1\}\{6\}z[^\n]{0,160}"
            r"=\\frac\{1-\\frac\{1\}\{6\}z\}",
        )
        wrong_modulus = _has(
            text,
            r"\|R\s*\(i(?:w|\\omega|y)\)\|\^2[^\n]{0,260}"
            r"1\s*\+\s*\\frac\{10\}\{9\}\s*(?:w|\\omega|y)\^2",
        )
        conflict = wrong_second_component or inconsistent_weighted_sum or wrong_modulus
        checks.append(
            CrossDomainCertificate(
                code="radau_internal_arithmetic",
                status="fail" if conflict else "pass",
                hard_failure=conflict,
                detail=(
                    "inverse_row_sum_or_imaginary_axis_modulus_conflict"
                    if conflict
                    else "no_detected_radau_internal_arithmetic_conflict"
                ),
            )
        )

    # Levy upward theorem: L1-bounded martingale convergence alone gives a.s. convergence,
    # not L1 convergence. Conditional expectations of one L1 variable are UI, which is the missing step.
    levy_candidate = _has(text, r"M_?n\s*=\s*\\mathbb\s*E\s*\[\s*X") or (
        _has(text, r"\\mathcal\s*F_?\\infty") and _has(text, r"Doob|鞅收敛")
    )
    if levy_candidate:
        false_doob_upgrade = _has(
            text,
            r"L\^?1\s*有界鞅[^。\n]{0,160}(?:Doob|鞅收敛)[^。\n]{0,180}"
            r"(?:几乎处处|a\.?s\.?).{0,80}(?:且|and).{0,40}L\^?1[^。\n]{0,40}收敛|"
            r"(?:Doob|martingale convergence)[^。\n]{0,220}L.?1\s+conver",
        )
        ui_established = _has(text, r"一致可积|uniformly integrable|uniform integrability")
        conflict = false_doob_upgrade and not ui_established
        checks.append(
            CrossDomainCertificate(
                code="levy_upward_requires_ui",
                status="fail" if conflict else "pass",
                hard_failure=conflict,
                detail="l1_boundedness_used_without_uniform_integrability" if conflict else "ui_precondition_not_omitted",
            )
        )

    # Holonomy: parallel transport around a curved loop need not return a vector to its original direction.
    holonomy_candidate = _has(text, r"holonomy|平行移动") and _has(text, r"d\\theta|d\s*theta|\\Delta\\theta")
    if holonomy_candidate:
        false_closed_return = _has(
            text,
            r"闭合回路[^。\n]{0,160}(?:向量|vector)[^。\n]{0,100}(?:回到|return)[^。\n]{0,80}"
            r"(?:原方向|原来的方向|same direction|original direction)|"
            r"(?:向量|vector)[^。\n]{0,100}(?:最终|最后|after one loop)[^。\n]{0,80}"
            r"(?:回到|return)[^。\n]{0,80}(?:原方向|same direction|original direction)",
        )
        checks.append(
            CrossDomainCertificate(
                code="holonomy_no_false_closed_return",
                status="fail" if false_closed_return else "pass",
                hard_failure=false_closed_return,
                detail="parallel_vector_forced_to_return_to_original_direction" if false_closed_return else "no_false_closed_loop_return_claim",
            )
        )

    return checks
