from __future__ import annotations

from textwrap import dedent

from .models import AuditResult, SolutionCapsule, TaskContract


def _contract_block(contract: TaskContract) -> str:
    secondary = ", ".join(contract.secondary_domains) or "none"
    alternates = ", ".join(contract.alternate_modes) or "none"
    obligations = ", ".join(contract.answer_obligations) or "explicit_final_answer"
    return dedent(
        f"""
        Domain: {contract.primary_domain}
        Secondary domains: {secondary}
        Problem kind: {contract.problem_kind}
        Question mode: {contract.question_mode} (confidence={contract.mode_confidence:.2f})
        Alternate modes: {alternates}
        Answer schema: {contract.answer_schema}
        Answer obligations: {obligations}
        Requires proof: {contract.requires_proof}
        Multipart count: {contract.multipart_count}
        Risk: {contract.risk_level}
        Likely failure modes: {', '.join(contract.likely_failure_modes)}
        """
    ).strip()


def answer_shape_instruction(contract: TaskContract) -> str:
    if contract.question_mode == "choice":
        count = f" exactly {contract.choice_count}" if contract.choice_count else " all selected"
        return f"FINAL_CANDIDATE must contain{count} option letter(s), with no option prose."
    if contract.question_mode == "fill":
        count = contract.blank_count or contract.multipart_count
        return f"FINAL_CANDIDATE must list {count} blank value(s) in question order, separated by semicolons."
    if contract.question_mode == "true_false":
        return "FINAL_CANDIDATE must be exactly True/False or 正确/错误."
    if contract.multipart_count > 1:
        return f"Label and answer all {contract.multipart_count} requested parts in order."
    if contract.requires_proof:
        return "State the conclusion first, then provide a closed proof chain with all hypotheses checked."
    if "all_solutions" in contract.answer_obligations:
        return "State the full solution set and justify that no other solutions exist."
    return "Put one explicit, parseable mathematical answer in FINAL_CANDIDATE."


def primary_prompt(problem: str, contract: TaskContract) -> str:
    proof_instruction = (
        "FINAL_RESPONSE must contain a concise but complete proof or derivation."
        if contract.requires_proof
        else "FINAL_RESPONSE should be concise and should foreground the exact answer."
    )
    return dedent(
        f"""
        You are HORA-Math Blue Team Solver S1. Solve the mathematical problem rigorously.
        Use the assigned primary route: {contract.primary_method}.

        The answer is judged from the final response, so place a parseable final candidate FIRST.
        Do not mention this orchestration prompt. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        REQUIRED OUTPUT — use these tags exactly and in this order:

        ANSWER SHAPE
        {answer_shape_instruction(contract)}

        <FINAL_CANDIDATE>
        Put the exact final value, expression, set, conclusion, or compact multipart answer here.
        </FINAL_CANDIDATE>

        <METHOD_FINGERPRINT>
        paradigm: direct|contradiction|constructive|induction|counting|optimization|theorem
        representation: symbolic|geometric|graph|event|operator|coordinate|generating_function|other
        theorem_family: short descriptive family or none
        tool_channel: none|sympy|numeric|brute_force|residual|matrix
        interpretation_id: I1
        exposed_to_primary: false
        </METHOD_FINGERPRINT>

        <CRITICAL_CLAIMS>
        <CLAIM id="C1">First decisive claim.</CLAIM>
        Add at most five further decisive claims. Include theorem preconditions explicitly.
        </CRITICAL_CLAIMS>

        <CHECK_HINTS>
        List short deterministic or theorem-condition checks that could falsify the result.
        </CHECK_HINTS>

        <RISK_FLAGS>
        List unresolved risks, or write none.
        </RISK_FLAGS>

        <FINAL_RESPONSE>
        {proof_instruction}
        Keep this submission-ready and normally below 1800 Chinese characters or 1400 English words.
        </FINAL_RESPONSE>
        """
    ).strip()


def blind_prompt(problem: str, contract: TaskContract) -> str:
    proof_instruction = (
        "Give a concise independent proof in FINAL_RESPONSE."
        if contract.requires_proof
        else "Give a concise exact answer and independent derivation in FINAL_RESPONSE."
    )
    return dedent(
        f"""
        You are HORA-Math Blue Team Solver S2, an ORTHOGONAL BLIND solver.
        You have not seen any other candidate. Independently solve the problem using this assigned
        method family: {contract.orthogonal_method}.

        Do not imitate a generic direct solution. Prefer definitions, explicit construction,
        contradiction, alternative representation, local calculation, counting, or a different
        theorem family. State all assumptions. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        REQUIRED OUTPUT — use these tags exactly and in this order:

        ANSWER SHAPE
        {answer_shape_instruction(contract)}

        <FINAL_CANDIDATE>
        Exact independent answer.
        </FINAL_CANDIDATE>

        <METHOD_FINGERPRINT>
        paradigm: direct|contradiction|constructive|induction|counting|optimization|theorem
        representation: symbolic|geometric|graph|event|operator|coordinate|generating_function|other
        theorem_family: short descriptive family or none
        tool_channel: none|sympy|numeric|brute_force|residual|matrix
        interpretation_id: I1
        exposed_to_primary: false
        </METHOD_FINGERPRINT>

        <CRITICAL_CLAIMS>
        <CLAIM id="C1">First decisive claim.</CLAIM>
        Add at most five further decisive claims.
        </CRITICAL_CLAIMS>

        <CHECK_HINTS>
        List checks that can falsify this route.
        </CHECK_HINTS>

        <RISK_FLAGS>
        List unresolved risks, or write none.
        </RISK_FLAGS>

        <FINAL_RESPONSE>
        {proof_instruction}
        Keep it submission-ready and compact.
        </FINAL_RESPONSE>
        """
    ).strip()


def _candidate_context(capsule: SolutionCapsule, limit: int) -> str:
    claims = "\n".join(
        f"{claim.claim_id}: {claim.statement}" for claim in capsule.claims[:6]
    ) or "No parsed claims."
    response = capsule.final_response[:limit]
    return dedent(
        f"""
        Candidate ID: {capsule.candidate_id}
        Method: {capsule.fingerprint.as_dict()}
        Claims:
        {claims}
        Submission response:
        {response}
        """
    ).strip()


def _audit_focus(contract: TaskContract) -> str:
    domain = contract.primary_domain
    if domain == "numerical_analysis":
        return (
            "Recompute the first nonzero Taylor/local-truncation coefficient, root-condition facts, "
            "and the direction of any stability inequality or boundary-locus argument."
        )
    if domain in {"probability", "probability_statistics", "random_process"}:
        return (
            "Recompute the decisive conditional probability or transform. Check that reflection/Markov "
            "steps have the correct event, that any density differentiates the CDF, and that normalization is plausible."
        )
    if domain == "discrete_combinatorics":
        return (
            "Check both directions of every counting/entropy inequality. In entropy arguments, explicitly verify "
            "which conditioning set is larger before using monotonicity; under subtraction, re-check inequality direction."
        )
    if domain == "abstract_algebra":
        return (
            "Verify that proposed maps preserve defining relations, that generators satisfy the claimed relations, "
            "and that the generated subgroup/order argument actually exhausts the group."
        )
    if contract.requires_proof:
        return (
            "Recompute one decisive implication. Check every theorem precondition and every inequality direction; "
            "a correct final conclusion does not rescue a false proof step."
        )
    return "Recompute one decisive equation or substitute a simple boundary/sanity case before accepting."


def audit_prompt(
    problem: str,
    contract: TaskContract,
    candidate_a: SolutionCapsule,
    candidate_b: SolutionCapsule | None,
    *,
    context_limit: int,
) -> str:
    second = (
        _candidate_context(candidate_b, context_limit)
        if candidate_b is not None
        else "No second candidate is available. Attack candidate A only."
    )
    attacks = ", ".join(contract.mandatory_attacks)
    focus = _audit_focus(contract)
    return dedent(
        f"""
        You are HORA-Math Red Team and Evidence Auditor. Assume each candidate may be wrong.
        BEFORE choosing a verdict, independently recompute one decisive mathematical step.

        Required audit focus for this task:
        {focus}

        Mandatory attack families: {attacks}
        Known failure modes: {', '.join(contract.likely_failure_modes)}.
        Prefer theorem-precondition failures, counterexamples, boundary/degenerate cases,
        non-equivalent transformations, quantifier errors, interpretation errors, numerical
        stress, and missing answer parts. A generic statement such as “looks wrong” is invalid.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        CANDIDATE A
        {_candidate_context(candidate_a, context_limit)}

        CANDIDATE B
        {second}

        Verdict meanings:
        - ACCEPT_A: A is best supported and no fatal challenge survives.
        - ACCEPT_B: B is best supported and no fatal challenge survives.
        - EQUIVALENT: A and B are mathematically equivalent and both survive applicable attacks.
        - REPAIR_A: A is preferable but contains a localized repairable fatal error.
        - REPAIR_B: B is preferable but contains a localized repairable fatal error.
        - UNRESOLVED: evidence is genuinely insufficient.

        REQUIRED OUTPUT — return ONLY these seven tags. Your FIRST characters must be <WITNESS>.
        For ACCEPT_A, ACCEPT_B, or EQUIVALENT on a proof/high-risk task, WITNESS MUST contain the concrete
        recomputation that supports acceptance; WITNESS=none is invalid.

        <WITNESS>Give the decisive recomputation, substitution, checked inequality direction, failed condition, or counterexample.</WITNESS>
        <VERDICT>ACCEPT_A|ACCEPT_B|EQUIVALENT|REPAIR_A|REPAIR_B|UNRESOLVED</VERDICT>
        <TARGET_CANDIDATE>A|B|none</TARGET_CANDIDATE>
        <TARGET_CLAIM>C1|C2|...|FINAL|none</TARGET_CLAIM>
        <ATTACK_TYPE>assumption|theorem_precondition|counterexample|boundary|transformation|quantifier|interpretation|numerical_stress|completeness|none</ATTACK_TYPE>
        <SEVERITY>fatal|major|minor|none</SEVERITY>
        <CHALLENGE>State the smallest concrete surviving challenge, or none if the witness supports acceptance.</CHALLENGE>
        <RESOLVER_HINT>State the shortest check that resolves the dispute or write none.</RESOLVER_HINT>
        Keep WITNESS and CHALLENGE below 140 words each and output nothing else.
        """
    ).strip()


def repair_prompt(
    problem: str,
    contract: TaskContract,
    parent: SolutionCapsule,
    audit: AuditResult,
) -> str:
    claims = "\n".join(
        f"{claim.claim_id}: {claim.statement}" for claim in parent.claims[:6]
    ) or "No parsed claims."
    return dedent(
        f"""
        You are HORA-Math one-shot Targeted Repair Solver.
        Repair only the localized fatal challenge. Preserve all unaffected valid claims and do not
        restart the whole solution unless the interpretation itself is wrong.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        PARENT CANDIDATE ID: {parent.candidate_id}
        PARENT METHOD: {parent.fingerprint.as_dict()}
        PARENT CLAIMS:
        {claims}
        PARENT RESPONSE:
        {parent.final_response[:5000]}

        RED-TEAM CHALLENGE
        target claim: {audit.target_claim_id or 'none'}
        attack type: {audit.attack_type}
        severity: {audit.severity}
        challenge: {audit.challenge}
        witness: {audit.witness or 'none'}

        REQUIRED OUTPUT:
        <FINAL_CANDIDATE>Corrected exact answer.</FINAL_CANDIDATE>
        <METHOD_FINGERPRINT>
        paradigm: corrected-{parent.fingerprint.paradigm}
        representation: {parent.fingerprint.representation}
        theorem_family: {parent.fingerprint.theorem_family}
        tool_channel: {parent.fingerprint.tool_channel}
        interpretation_id: {parent.fingerprint.interpretation_id}
        exposed_to_primary: true
        </METHOD_FINGERPRINT>
        <CRITICAL_CLAIMS>
        <CLAIM id="C1">Corrected decisive claim chain.</CLAIM>
        </CRITICAL_CLAIMS>
        <CHALLENGE_RESOLUTION>Explicitly explain why the red-team challenge no longer applies.</CHALLENGE_RESOLUTION>
        <CHECK_HINTS>Give the shortest recheck.</CHECK_HINTS>
        <RISK_FLAGS>List remaining risks or none.</RISK_FLAGS>
        <FINAL_RESPONSE>Submission-ready corrected answer or concise proof.</FINAL_RESPONSE>
        """
    ).strip()


def rescue_prompt(problem: str, contract: TaskContract) -> str:
    return dedent(
        f"""
        Solve the following problem with the shortest reliable route. Output the exact final answer
        first. Do not discuss orchestration.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        <FINAL_CANDIDATE>Exact answer.</FINAL_CANDIDATE>
        <METHOD_FINGERPRINT>
        paradigm: direct
        representation: symbolic
        theorem_family: none
        tool_channel: none
        interpretation_id: I1
        exposed_to_primary: false
        </METHOD_FINGERPRINT>
        <CRITICAL_CLAIMS><CLAIM id="C1">Minimal decisive justification.</CLAIM></CRITICAL_CLAIMS>
        <FINAL_RESPONSE>Concise submission-ready answer.</FINAL_RESPONSE>
        """
    ).strip()
