from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DerivationCertificate:
    code: str
    status: str
    hard_failure: bool
    detail: str


def _has(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, str(text or ""), flags=re.IGNORECASE | re.DOTALL))


def evaluate_decisive_derivation_certificates(
    *,
    answer_raw: str,
    response: str,
    requirements: tuple[str, ...],
) -> list[DerivationCertificate]:
    """Deterministic checks for proof-shape errors that semantic review can easily miss.

    Certificates are activated by explicit task language or a distinctive derivation in the
    candidate. They never compare with benchmark answer fields.
    """

    answer = str(answer_raw or "").strip()
    text = str(response or "")
    req = "\n".join(str(item or "") for item in requirements)
    checks: list[DerivationCertificate] = []

    dangling = bool(
        answer
        and re.search(
            r"(?:为|是|等于|得到|可得|如下|[:：=]|\b(?:is|equals|are)\s*)$",
            answer,
            flags=re.IGNORECASE,
        )
    )
    checks.append(
        DerivationCertificate(
            code="explicit_final_candidate_complete",
            status="fail" if dangling else "pass",
            hard_failure=dangling,
            detail="dangling_answer_cue" if dangling else "candidate_has_closed_conclusion",
        )
    )

    # Shearer/Han entropy chain.
    shearer_requested = _has(req + "\n" + text, r"shearer") and _has(
        req, r"条件越多.*条件熵越小|conditioning reduces entropy"
    )
    if shearer_requested:
        ordered_prefix = (
            _has(text, r"Z_1\s*,?\s*\\dots\s*,?\s*Z_\{?j-1\}?")
            or _has(text, r"S\s*\\cap\s*\\?\{?1\s*,?\s*\\dots\s*,?\s*j-1")
            or _has(text, r"前\s*j-1\s*个坐标|previous\s+j-1\s+coordinates")
            or _has(text, r"固定坐标顺序|fix(?:ed)?\s+(?:a\s+)?coordinate\s+order")
        )
        false_marginal_domination = _has(
            text,
            r"(?:得到|推出|故|因此|hence|therefore)[^\n。]{0,80}"
            r"H\s*\(\s*Z\s*\)\s*(?:<=|≤|\\le)\s*H\s*\(\s*Z_\{?-i\}?\s*\)",
        )
        reversed_prefix_vs_full = _has(
            text,
            r"H\s*\(\s*Z_i\s*\\?mid\s*Z_1\s*,\s*\\dots\s*,\s*Z_\{?i-1\}?\s*\)\s*"
            r"(?:\\le|≤)\s*H\s*\(\s*Z_i\s*\\?mid\s*Z_\{?-i\}?\s*\)",
        )
        reversed_by_words = (
            _has(text, r"Z_\{?-i\}?.{0,140}(?:包含|contains).{0,140}Z_1.{0,100}Z_\{?i-1\}?")
            and _has(text, r"条件越多.{0,30}条件熵越小|conditioning reduces entropy")
            and _has(
                text,
                r"H\s*\(\s*Z_i[^\n]{0,180}Z_\{?i-1\}?[^\n]{0,50}\)\s*(?:\\le|≤)\s*"
                r"H\s*\(\s*Z_i[^\n]{0,120}Z_\{?-i\}?[^\n]{0,30}\)",
            )
        )
        wrong_conditioning_direction = (
            _has(text, r"条件集合.{0,120}(?:多|larger|more variables)")
            and _has(
                text,
                r"H\s*\(\s*Z_j[^\n]{0,220}\\?mid[^\n]{0,220}\)\s*\\?le\s*H\s*\(\s*Z_j[^\n]{0,140}Z_\{?j-1\}?[^\n]{0,40}\)",
            )
            and _has(
                text,
                r"\\sum_\{?i=1\}?\^?\{?d\}?\s*H\s*\(\s*Z_\{?-i\}?\s*\)\s*\\?ge|"
                r"sum.{0,80}H\s*\(\s*Z_\{?-i\}?\s*\).{0,80}(?:>=|\\ge)",
            )
        )
        safe_less_conditioning = (
            _has(text, r"少一个条件|条件更少|less conditioning|fewer conditioning")
            and _has(text, r"H\s*\(\s*Z_j[^\n]{0,220}\\?mid[^\n]{0,220}\)\s*\\?ge")
        )
        explicit_reversal = reversed_prefix_vs_full or reversed_by_words
        ok = (
            ordered_prefix
            and not false_marginal_domination
            and not wrong_conditioning_direction
            and not explicit_reversal
        )
        if safe_less_conditioning and not false_marginal_domination and not explicit_reversal:
            ok = True
        checks.append(
            DerivationCertificate(
                code="shearer_ordered_conditioning_chain",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail=(
                    "ordered_less_conditioning_chain_present"
                    if ok
                    else (
                        "prefix_vs_full_conditioning_inequality_reversed"
                        if explicit_reversal
                        else (
                            "false_HZ_le_HZminus_i_shortcut_present"
                            if false_marginal_domination
                            else (
                                "conditioning_monotonicity_direction_conflicts_with_shearer_lower_bound"
                                if wrong_conditioning_direction
                                else "missing_non_circular_ordered_conditioning_argument"
                            )
                        )
                    )
                ),
            )
        )

    # BDF2 local consistency.
    bdf2_like = _has(req + "\n" + text, r"BDF2|局部截断误差|local truncation") and _has(
        text, r"3\s*y|3y|3\\?zeta\^?2"
    )
    if bdf2_like:
        stated_half = _has(
            text,
            r"y\s*\(\s*t_\{?n\+1\}?\s*\).{0,300}\\frac\{h\^2\}\{2\}\s*y''",
        )
        substitution_drops_half = _has(
            text,
            r"-\s*4\s*\\?(?:Bigl|bigl)?\s*\([^\n]{0,180}\\frac\{h\^2\}\s*y''(?!\s*/?\s*2)",
        ) or _has(
            text,
            r"-\s*4\s*\\?(?:Bigl|bigl)?\s*\([^\n]{0,180}h\^2\s*y''(?!\s*/?\s*2)",
        )
        conflict = stated_half and substitution_drops_half
        checks.append(
            DerivationCertificate(
                code="bdf2_taylor_substitution_consistency",
                status="fail" if conflict else "pass",
                hard_failure=conflict,
                detail="h2_over_2_lost_during_substitution" if conflict else "no_detected_taylor_substitution_conflict",
            )
        )

        wrong_third_derivative_sign = _has(
            text,
            r"\\frac\{3y[^\n]{0,180}\}\{2h\}\s*=\s*y'[^\n]{0,100}"
            r"\+\s*\\frac\{h\^2\}\{3\}\s*y'''",
        ) or _has(
            text,
            r"差分商[^\n]{0,200}=\s*y'[^\n]{0,100}\+\s*\\frac\{h\^2\}\{3\}\s*y'''",
        )
        checks.append(
            DerivationCertificate(
                code="bdf2_third_derivative_sign",
                status="fail" if wrong_third_derivative_sign else "pass",
                hard_failure=wrong_third_derivative_sign,
                detail="bdf2_difference_quotient_third_derivative_sign_reversed" if wrong_third_derivative_sign else "no_detected_bdf2_third_derivative_sign_conflict",
            )
        )

        z_minus_one = _has(text, r"z\s*=\s*-\s*1")
        missing_constant_at_anchor = z_minus_one and (
            _has(text, r"5\s*\\?zeta\^2\s*-\s*4\s*\\?zeta\s*=\s*0")
            or _has(text, r"5\s*ζ\^2\s*-\s*4\s*ζ\s*=\s*0")
            or _has(text, r"根[^\n]{0,90}(?:0\s*,\s*4/5|0\s*和\s*4/5)")
        )
        checks.append(
            DerivationCertificate(
                code="bdf2_negative_anchor_equation",
                status="fail" if missing_constant_at_anchor else "pass",
                hard_failure=missing_constant_at_anchor,
                detail="constant_term_plus_one_lost_at_z_minus_one" if missing_constant_at_anchor else "no_detected_negative_anchor_equation_conflict",
            )
        )

    bdf2_branch_requested = _has(req, r"边界轨迹|根轨迹|boundary locus|root locus") and _has(
        req, r"割裂|稳定分支|左半平面|disconnect|stable branch|left half"
    )
    if bdf2_branch_requested and _has(text, r"BDF2|3\s*y_\{?n\+2\}?|3\s*-\s*4e"):
        negative_anchor = _has(
            text,
            r"z\s*=\s*-\s*\d|z\s*<\s*0|负实数|负实轴|negative real|z\s*\\to\s*-\\infty|z\s*→\s*-∞",
        )
        anchor_verified = _has(
            text,
            r"模(?:均|都)?.{0,60}(?:<|小于)\s*1|\|\\?(?:xi|zeta|ξ|ζ).{0,20}\|\s*<\s*1|"
            r"inside the unit (?:disk|circle)|根.{0,80}(?:趋于|趋近|tend(?:s|ing)? to)\s*0",
        )
        ok = negative_anchor and anchor_verified
        checks.append(
            DerivationCertificate(
                code="stable_branch_interior_anchor",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail="left_half_plane_anchor_verified" if ok else "missing_verified_interior_stable_anchor",
            )
        )

    # Scalar probability cannot equal a conditional-expectation random variable.
    conditional_scalar_mismatch = _has(
        text,
        r"\\mathbb\s*P\s*\([^\n=]{1,180}\)\s*=\s*\\mathbb\s*E\s*(?:\\Big)?\[\s*\\mathbf\s*1[^\]]{0,260}\\mid\s*\\mathcal\s*F",
    )
    if conditional_scalar_mismatch:
        checks.append(
            DerivationCertificate(
                code="conditional_expectation_type_consistency",
                status="fail",
                hard_failure=True,
                detail="scalar_probability_set_equal_to_conditional_random_variable",
            )
        )

    # Two-stage Radau IIA: catch internal arithmetic contradictions in an otherwise correct final R(z).
    radau_like = _has(req + "\n" + text, r"Radau\s*IIA") or (
        _has(text, r"R\s*\(z\)\s*=.*1\s*\+\s*z/3")
        and _has(text, r"1\s*-\s*2z/3.*z\^2/6")
    )
    if radau_like:
        wrong_inverse_vector = _has(
            text,
            r"\(I-zA\)\^\{-1\}\\mathbf\s*1.{0,320}1\s*-\s*\\frac\{1\}\{6\}\s*z",
        )
        wrong_axis_modulus = _has(
            text,
            r"\|R\s*\(i\\?omega\)\|\^2.{0,420}1\s*\+\s*\\?omega\^2/3\s*\+\s*\\?omega\^4/36",
        ) or _has(
            text,
            r"\|R\s*\(iy\)\|\^2.{0,420}1\s*\+\s*y\^2/3\s*\+\s*y\^4/36",
        )
        conflict = wrong_inverse_vector or wrong_axis_modulus
        checks.append(
            DerivationCertificate(
                code="runge_kutta_stability_arithmetic",
                status="fail" if conflict else "pass",
                hard_failure=conflict,
                detail=(
                    "inverse_vector_arithmetic_conflict"
                    if wrong_inverse_vector
                    else ("imaginary_axis_modulus_coefficient_conflict" if wrong_axis_modulus else "no_detected_rk_arithmetic_conflict")
                ),
            )
        )

    # Levy upward theorem: L1-bounded/nonnegative martingale convergence alone does not give L1 convergence.
    levy_upward_like = _has(req, r"\\mathcal\s*F_?n|F_n") and _has(
        req, r"条件期望|conditional expectation|\\mathbb\s*E\s*\[\s*X"
    ) and _has(req, r"L\^?1|L_1")
    if levy_upward_like:
        false_doob_l1 = _has(
            text,
            r"非负.{0,100}(?:L\^?1|L_1).{0,80}有界.{0,180}(?:Doob|鞅收敛).{0,180}(?:L\^?1|L_1).{0,40}收敛|"
            r"nonnegative.{0,100}L.?1.{0,80}bounded.{0,180}martingale convergence.{0,180}L.?1 convergence",
        )
        invalid_x_approximation = _has(
            text,
            r"取\s*Y.{0,100}\\mathcal\s*F_?N.{0,50}可测.{0,120}\\?\|\s*X\s*-\s*Y\s*\\?\|_?1\s*<\s*\\?varepsilon",
        )
        conflict = false_doob_l1 or invalid_x_approximation
        checks.append(
            DerivationCertificate(
                code="levy_upward_uniform_integrability",
                status="fail" if conflict else "pass",
                hard_failure=conflict,
                detail=(
                    "l1_bounded_martingale_incorrectly_promoted_to_l1_convergence"
                    if false_doob_l1
                    else ("approximated_arbitrary_X_by_Fn_measurable_variables" if invalid_x_approximation else "no_detected_levy_upward_precondition_conflict")
                ),
            )
        )

    # Holonomy: a parallel vector generally does not return with the same direction; the sign must follow
    # directly from dtheta=-omega and domega=-K dA, not be discarded modulo 2pi.
    holonomy_like = _has(req, r"平行移动|parallel transport|holonomy") and _has(
        req, r"Gauss.?Bonnet|联络\s*1-?形式|connection\s*1-?form"
    )
    if holonomy_like:
        false_return = _has(
            text,
            r"回到起点.{0,50}(?:方向不变|direction unchanged|same direction)|"
            r"returns?.{0,60}(?:unchanged|same)\s+direction",
        )
        sign_absorption = _has(
            text,
            r"负号.{0,80}(?:方向约定|orientation).{0,60}(?:吸收|absorb)|"
            r"-\\int[^\n]{0,100}\\equiv\s*\\int[^\n]{0,80}(?:pmod|mod)",
        )
        conflict = false_return or sign_absorption
        checks.append(
            DerivationCertificate(
                code="holonomy_orientation_consistency",
                status="fail" if conflict else "pass",
                hard_failure=conflict,
                detail=(
                    "parallel_vector_incorrectly_assumed_to_return_unchanged"
                    if false_return
                    else ("curvature_integral_sign_discarded_mod_2pi" if sign_absorption else "no_detected_holonomy_orientation_conflict")
                ),
            )
        )

    # If the statement explicitly demands Brownian motion relative to the original filtration, replacing
    # it by the natural filtration proves a weaker statement and does not satisfy the contract.
    original_filtration_required = _has(req, r"原滤过|original filtration")
    if original_filtration_required:
        natural_filtration = _has(text, r"自然滤过|natural filtration|\\mathcal\s*F_?t\^M|\\mathcal\s*F_?s\^M")
        original_filtration_used = _has(text, r"原滤过|original filtration")
        conflict = natural_filtration and not original_filtration_used
        checks.append(
            DerivationCertificate(
                code="original_filtration_obligation",
                status="fail" if conflict else "pass",
                hard_failure=conflict,
                detail="proved_only_natural_filtration_statement" if conflict else "original_filtration_not_replaced",
            )
        )

    # James--Stein range: an open interval is the strict-improvement range, not the full non-increase range.
    james_stein_like = _has(text, r"Stein\s*(?:恒等式|identity)|James.?Stein") and _has(
        text, r"\\delta_?a|delta_?a"
    )
    if james_stein_like:
        open_interval_as_iff_nonincrease = _has(
            text,
            r"当且仅当\s*0\s*<\s*a\s*<\s*2\s*\(?p\s*-\s*2\)?[^。\n]{0,180}(?:风险不增|R\s*\([^\n]{0,80}\\le)|"
            r"iff\s*0\s*<\s*a\s*<\s*2\s*\(?p\s*-\s*2\)?.{0,180}risk.{0,40}(?:non.?increase|<=)",
        )
        checks.append(
            DerivationCertificate(
                code="james_stein_endpoint_range",
                status="fail" if open_interval_as_iff_nonincrease else "pass",
                hard_failure=open_interval_as_iff_nonincrease,
                detail="strict_interval_mistaken_for_full_nonincrease_range" if open_interval_as_iff_nonincrease else "no_detected_james_stein_endpoint_conflict",
            )
        )

    return checks
