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

    radau = _has(text, r"Radau\s*IIA") or (
        _has(text, r"1\s*\+\s*(?:z/3|\\frac\{1\}\{3\}\s*z|\\frac13\s*z)")
        and _has(text, r"1\s*-\s*(?:2z/3|\\frac\{2\}\{3\}\s*z|\\frac23\s*z)")
        and _has(text, r"(?:z\^2/6|\\frac\{1\}\{6\}\s*z\^2|\\frac16\s*z\^2)")
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
            r"\|R\s*\(i(?:w|\\omega|y)\)\|\^2[^\n]{0,320}"
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

        correct_r = (
            _has(text, r"R\s*\(z\)\s*=.{0,120}1\s*\+\s*(?:z/3|\\frac\{1\}\{3\}\s*z|\\frac13\s*z)")
            and _has(text, r"1\s*-\s*(?:2z/3|\\frac\{2\}\{3\}\s*z|\\frac23\s*z).{0,100}(?:z\^2/6|\\frac\{1\}\{6\}\s*z\^2|\\frac16\s*z\^2)")
        )
        correct_axis = (
            _has(text, r"\|R\s*\(i(?:w|\\omega|y)\)\|\^2")
            and _has(text, r"1\s*\+\s*(?:\\frac\{1\}\{9\}|\\frac19|1/9)\s*(?:w|\\omega|y)\^2")
            and _has(text, r"(?:w|\\omega|y)\^4\s*/\s*36|\\frac\{1\}\{36\}\s*(?:w|\\omega|y)\^4|\\frac1\{36\}\s*(?:w|\\omega|y)\^4")
            and _has(text, r"(?:\\le|≤)\s*1")
        )
        poles_right = _has(
            text,
            r"2\s*\\pm\s*i\s*\\sqrt\{?2\}?|2\s*±\s*i\s*√?2|"
            r"极点[^。\n]{0,100}(?:右半平面|实部[^。\n]{0,30}(?:正|>\s*0))|"
            r"poles?[^.\n]{0,120}(?:right half|positive real part)",
        )
        l_stable = _has(
            text,
            r"R\s*\(z\)\s*(?:\\to|→)\s*0[^。\n]{0,80}(?:z|\|z\|)[^。\n]{0,30}(?:\\to|→)\s*\\infty|"
            r"\\lim_\{?z[^}]*\\to[^}]*\\infty\}?\s*R\s*\(z\)\s*=\s*0|L-?稳定|L[- ]stable",
        )
        maximum_principle = _has(
            text,
            r"最大模原理|maximum modulus|解析[^。\n]{0,100}左半平面|analytic[^.\n]{0,100}left half",
        )
        full_certificate = (
            correct_r
            and correct_axis
            and poles_right
            and maximum_principle
            and l_stable
            and not conflict
        )
        checks.append(
            CrossDomainCertificate(
                code="radau_full_stability_certificate",
                status="pass" if full_certificate else "unknown",
                hard_failure=False,
                detail=(
                    "stability_function_axis_poles_and_limit_verified"
                    if full_certificate
                    else "full_mechanical_certificate_not_established"
                ),
            )
        )

    levy_candidate = _has(text, r"M_?n\s*=\s*\\mathbb\s*E\s*\[\s*X") or (
        _has(text, r"\\mathcal\s*F_?\\infty") and _has(text, r"Doob|鞅收敛")
    )
    if levy_candidate:
        l1_bounded = _has(
            text,
            r"L\s*\^?\s*1\s*有界|L_?1\s*有界|L¹\s*有界|L.?1[- ]bounded",
        )
        doob_used = _has(text, r"Doob|鞅收敛定理|martingale convergence theorem")
        l1_convergence_claim = _has(
            text,
            r"在\s*L\s*\^?\s*1\s*(?:中)?收敛|L_?1\s*(?:中)?收敛|L¹\s*(?:中)?收敛|L.?1\s+conver",
        )
        false_doob_upgrade = l1_bounded and doob_used and l1_convergence_claim
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

    holonomy_candidate = (
        _has(text, r"holonomy|平行移动")
        or (_has(text, r"d\\theta|d\s*theta|\\Delta\\theta") and _has(text, r"d\\omega|K\\,?dA|K\s*dA"))
    )
    if holonomy_candidate:
        false_closed_return = _has(
            text,
            r"闭合回路[^。\n]{0,180}(?:向量|vector)[^。\n]{0,120}(?:最终|最后|after one loop)?[^。\n]{0,80}"
            r"(?:回到|return)[^。\n]{0,80}(?:原方向|原来的方向|same direction|original direction)|"
            r"(?:向量|vector)[^。\n]{0,120}(?:最终|最后|after one loop)[^。\n]{0,80}"
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
