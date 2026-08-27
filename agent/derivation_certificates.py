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

    The certificates are activated by explicit task language or by a distinctive mathematical
    derivation already present in the candidate. They do not compare against benchmark answers.
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

    # Shearer/Han-style entropy proofs require a non-circular use of conditioning monotonicity.
    # The safe chain-rule route conditions each coordinate on an ordered prefix (or the
    # corresponding prefix restricted to a covering set). Merely writing
    # H(Z_i|Z_-i) <= H(Z) and rearranging is not a proof of Shearer.
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
        suspicious_shortcut = _has(
            text,
            r"H\s*\(\s*Z_i\s*\\?mid\s*Z_\{?-i\}?\s*\)\s*\\?le\s*H\s*\(\s*Z\s*\)",
        )
        ok = ordered_prefix and not (suspicious_shortcut and not ordered_prefix)
        checks.append(
            DerivationCertificate(
                code="shearer_ordered_conditioning_chain",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail=(
                    "ordered_prefix_chain_present"
                    if ok
                    else "missing_non_circular_ordered_conditioning_argument"
                ),
            )
        )

    # If the task explicitly asks why a boundary locus cannot disconnect the stable branch,
    # the proof needs at least one interior stable anchor in the left half-plane (or an
    # equivalent explicit local-continuation argument). The boundary point z=0 alone is not enough.
    bdf2_branch_requested = _has(req, r"边界轨迹|根轨迹|boundary locus|root locus") and _has(
        req, r"割裂|稳定分支|左半平面|disconnect|stable branch|left half"
    )
    if bdf2_branch_requested and _has(text, r"BDF2|3\s*y_\{?n\+2\}?|3\s*-\s*4e"):
        negative_anchor = _has(
            text,
            r"z\s*=\s*-\s*\d|z\s*<\s*0|负实数|负实轴|negative real",
        )
        anchor_verified = _has(
            text,
            r"模(?:均|都)?.{0,60}(?:<|小于)\s*1|\|\\?(?:xi|zeta|ξ|ζ).{0,20}\|\s*<\s*1|inside the unit (?:disk|circle)",
        )
        ok = negative_anchor and anchor_verified
        checks.append(
            DerivationCertificate(
                code="stable_branch_interior_anchor",
                status="pass" if ok else "fail",
                hard_failure=not ok,
                detail=(
                    "left_half_plane_anchor_verified"
                    if ok
                    else "missing_verified_interior_stable_anchor"
                ),
            )
        )

    # A scalar probability cannot equal a conditional expectation random variable. The valid
    # tower-property statement is P(E)=E[E[1_E|F_t]] or directly P(E)=E[q(B_t)].
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

    return checks
