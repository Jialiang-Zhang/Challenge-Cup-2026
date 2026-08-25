from __future__ import annotations

import re

from .models import AuditResult, EvidenceRecord, SolutionCapsule, TaskContract


def _compact(value: str) -> str:
    value = value.lower()
    value = value.replace("\\left", "").replace("\\right", "")
    value = value.replace("$", "").replace("`", "")
    return re.sub(r"\s+", "", value)


def _candidate_text(capsule: SolutionCapsule) -> str:
    claims = "\n".join(claim.statement for claim in capsule.claims)
    hints = "\n".join(capsule.check_hints)
    return "\n".join((capsule.answer_raw, capsule.final_response, claims, hints))


def _evidence(
    capsule: SolutionCapsule,
    evidence_type: str,
    *,
    status: str,
    strength: str,
    detail_code: str | None,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=f"DOMAIN-{capsule.candidate_id}-{evidence_type}",
        candidate_id=capsule.candidate_id,
        evidence_type=evidence_type,
        status=status,  # type: ignore[arg-type]
        strength=strength,
        checker="domain_obligation_checker",
        detail_code=detail_code,
    )


def is_matrix_tree_spectrum_problem(problem: str) -> bool:
    lowered = problem.lower()
    return (
        ("矩阵树" in problem or "matrix-tree" in lowered or "matrix tree" in lowered)
        and ("特征值" in problem or "spectrum" in lowered or "eigenvalue" in lowered)
    )


def is_l1_weak_norm_problem(problem: str) -> bool:
    compact = _compact(problem)
    has_l1 = any(token in compact for token in ("l^1", "l^{1}", "l_1", "l1"))
    return has_l1 and ("弱收敛" in problem or "weakconverg" in compact)


def is_group_order_p3_problem(problem: str) -> bool:
    compact = _compact(problem)
    return (
        ("p^3" in compact or "p^{3}" in compact)
        and ("z(g)" in compact or "中心" in problem)
        and ("群" in problem or "group" in compact)
    )


def solver_obligations(problem: str, contract: TaskContract) -> tuple[str, ...]:
    obligations: list[str] = []
    if contract.requires_proof:
        obligations.extend(
            (
                "Every theorem used must have its hypotheses checked explicitly.",
                "The proof must establish every requested necessity, sufficiency, existence, and uniqueness component.",
            )
        )

    if is_matrix_tree_spectrum_problem(problem):
        obligations.extend(
            (
                "For a connected N-vertex graph, explicitly use tau(G)=(1/N) times the product of all nonzero Laplacian eigenvalues.",
                "For K_{m,n}, the complete Laplacian spectrum must include 0, m with multiplicity n-1, n with multiplicity m-1, and m+n with multiplicity 1.",
                "Check that the eigenvalue multiplicities sum to m+n and that K_{2,2} gives four spanning trees.",
            )
        )

    if is_l1_weak_norm_problem(problem):
        obligations.extend(
            (
                "Any claimed L1 counterexample must verify all three facts: weak convergence against every L-infinity test function, exact norm convergence, and failure of strong convergence.",
                "Do not use shrinking spikes as a weakly-null example without a valid proof; a standard valid witness is f_n=1+r_n with Rademacher functions r_n.",
            )
        )

    if is_group_order_p3_problem(problem):
        obligations.extend(
            (
                "Use the class equation or the nontrivial-center theorem for finite p-groups.",
                "Explain why |Z(G)| at least p^2 makes G/Z(G) cyclic and why a cyclic central quotient forces G to be abelian.",
                "When |Z(G)|=p, identify the quotient of order p^2 as C_p times C_p, not merely an unspecified abelian group.",
            )
        )
    return tuple(obligations)


def audit_obligations(problem: str, contract: TaskContract) -> tuple[str, ...]:
    obligations = list(solver_obligations(problem, contract))
    obligations.extend(
        (
            "An acceptance verdict must report a concrete falsification check in WITNESS and the shortest reproducible check in RESOLVER_HINT.",
            "A proposed counterexample is not evidence until every hypothesis and the claimed failure have both been verified.",
        )
    )
    return tuple(obligations)


def evaluate_domain_obligations(
    problem: str,
    capsule: SolutionCapsule,
    contract: TaskContract,
) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []
    text = _candidate_text(capsule)
    compact = _compact(text)

    if is_matrix_tree_spectrum_problem(problem):
        has_zero = "0" in compact and any(
            token in compact for token in ("特征值", "eigenvalue", "spectrum", "谱")
        )
        has_m = "m" in compact and any(
            token in compact for token in ("n-1", "n−1", "n-1重", "multiplicityn-1")
        )
        has_n = "n" in compact and any(
            token in compact for token in ("m-1", "m−1", "m-1重", "multiplicitym-1")
        )
        has_m_plus_n = any(token in compact for token in ("m+n", "n+m"))
        spectrum_ok = has_zero and has_m and has_n and has_m_plus_n
        records.append(
            _evidence(
                capsule,
                "matrix_tree_complete_spectrum",
                status="pass" if spectrum_ok else "fail",
                strength="structural" if spectrum_ok else "hard",
                detail_code=None if spectrum_ok else "missing_zero_m_n_or_m_plus_n_eigenvalue",
            )
        )

        factor_patterns = (
            r"\\frac\{1\}\{(?:m\+n|n\+m)\}",
            r"1/\((?:m\+n|n\+m)\)",
            r"(?:除以|divideby)(?:m\+n|n\+m)",
        )
        has_factor = any(re.search(pattern, compact) for pattern in factor_patterns)
        records.append(
            _evidence(
                capsule,
                "matrix_tree_spectral_divisor",
                status="pass" if has_factor else "fail",
                strength="structural" if has_factor else "hard",
                detail_code=None if has_factor else "missing_one_over_vertex_count_factor",
            )
        )

    if is_l1_weak_norm_problem(problem):
        answer_letters = set(re.findall(r"[ABCD]", capsule.answer_raw.upper()))
        selects_d = "D" in answer_letters
        rademacher = any(token in compact for token in ("rademacher", "拉德马赫", "r_n", "r_{n}"))
        one_plus_r = any(token in compact for token in ("1+r_n", "1+r_{n}", "1+rn"))
        valid_standard_witness = rademacher and one_plus_r
        spike_witness = (
            ("\\chi" in compact or "χ" in text)
            and "1/n" in compact
            and re.search(r"(?:^|[^a-z])n(?:\\chi|χ)", compact) is not None
        )

        if spike_witness:
            records.append(
                _evidence(
                    capsule,
                    "l1_counterexample_witness",
                    status="fail",
                    strength="hard",
                    detail_code="shrinking_spike_does_not_establish_norm_preservation_and_weak_nullity",
                )
            )
        elif selects_d and valid_standard_witness:
            records.append(
                _evidence(
                    capsule,
                    "l1_counterexample_witness",
                    status="pass",
                    strength="structural",
                    detail_code="rademacher_counterexample_present",
                )
            )
        elif selects_d:
            records.append(
                _evidence(
                    capsule,
                    "l1_counterexample_witness",
                    status="fail",
                    strength="hard",
                    detail_code="option_d_selected_without_a_verified_l1_counterexample",
                )
            )

    if is_group_order_p3_problem(problem):
        center_argument = any(
            token in compact
            for token in ("类方程", "classequation", "p群中心非平凡", "nontrivialcenter")
        )
        cyclic_quotient = (
            any(token in compact for token in ("g/z(g)", "商群", "quotient"))
            and any(token in compact for token in ("循环", "cyclic"))
            and any(token in compact for token in ("阿贝尔", "abelian"))
        )
        elementary_abelian = any(
            token in compact
            for token in (
                "c_p\\timesc_p",
                "c_p×c_p",
                "c_p\timesc_p",
                "c_p\\oplusc_p",
                "初等阿贝尔",
                "elementaryabelian",
            )
        )
        group_ok = center_argument and cyclic_quotient and elementary_abelian
        records.append(
            _evidence(
                capsule,
                "p3_group_proof_obligations",
                status="pass" if group_ok else "fail",
                strength="structural" if group_ok else "hard",
                detail_code=None if group_ok else "missing_center_cyclic_quotient_or_elementary_abelian_step",
            )
        )

    return records


def audit_coverage(
    problem: str,
    contract: TaskContract,
    audit: AuditResult,
) -> tuple[bool, str | None]:
    if audit.verdict not in {"ACCEPT_A", "ACCEPT_B", "EQUIVALENT"}:
        return True, None

    if contract.risk_level in {"high", "critical"} or contract.requires_proof:
        if audit.attack_type in {"", "none"}:
            return False, "high_risk_acceptance_without_attack_family"
        if audit.witness is None or audit.resolver_hint is None:
            return False, "high_risk_acceptance_without_reproducible_check"

    proof = _compact("\n".join(filter(None, (audit.witness, audit.resolver_hint))))
    if is_matrix_tree_spectrum_problem(problem):
        has_m_plus_n = any(token in proof for token in ("m+n", "n+m"))
        has_factor_check = any(
            token in proof
            for token in ("1/(m+n)", "1/(n+m)", "乘积", "product", "k_{2,2}", "k2,2")
        )
        if not (has_m_plus_n and has_factor_check):
            return False, "matrix_tree_acceptance_missing_spectrum_and_divisor_check"

    if is_l1_weak_norm_problem(problem):
        has_weak = any(token in proof for token in ("weak", "弱收敛", "l∞", "l^\\infty"))
        has_norm = any(token in proof for token in ("norm", "范数", "||", "\\|"))
        if not (has_weak and has_norm):
            return False, "l1_acceptance_missing_weak_and_norm_check"

    if is_group_order_p3_problem(problem):
        has_center = any(token in proof for token in ("center", "中心", "类方程"))
        has_quotient = any(token in proof for token in ("quotient", "商群", "g/z(g)"))
        if not (has_center and has_quotient):
            return False, "p3_acceptance_missing_center_and_quotient_check"

    return True, None
