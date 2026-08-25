from __future__ import annotations

from textwrap import dedent

from .models import TaskContract


def _contract_block(contract: TaskContract) -> str:
    secondary = ", ".join(contract.secondary_domains) or "none"
    return dedent(
        f"""
        Domain: {contract.primary_domain}
        Secondary domains: {secondary}
        Problem kind: {contract.problem_kind}
        Answer schema: {contract.answer_schema}
        Requires proof: {contract.requires_proof}
        Multipart count: {contract.multipart_count}
        Risk: {contract.risk_level}
        Likely failure modes: {', '.join(contract.likely_failure_modes)}
        """
    ).strip()


def _strict_protocol_block(response_requirement: str) -> str:
    return dedent(
        f"""
        OUTPUT CONTRACT
        - Start the response immediately with the opening tag <FINAL_CANDIDATE>.
        - Inside that tag, write the actual computed mathematical answer, never an instruction.
        - Close it with </FINAL_CANDIDATE> before writing any explanation.
        - Never copy phrases such as "Exact independent answer", "Exact answer",
          "First decisive claim", "Give a concise...", or "..." into any field.
        - Emit the remaining fields in the exact order below and stop after </FINAL_RESPONSE>.
        - Do not write analysis, a preamble, Markdown fences, or commentary outside the tags.

        <METHOD_FINGERPRINT>
        paradigm: choose one of direct|contradiction|constructive|induction|counting|optimization|theorem
        representation: choose one of symbolic|geometric|graph|event|operator|coordinate|generating_function|other
        theorem_family: write the actual short theorem or method family, or none
        tool_channel: choose one of none|sympy|numeric|brute_force|residual|matrix
        interpretation_id: I1
        exposed_to_primary: false
        </METHOD_FINGERPRINT>

        <CRITICAL_CLAIMS>
        Write one to six actual decisive claims. Each claim must use the form
        <CLAIM id="C1">a concrete mathematical statement</CLAIM>.
        </CRITICAL_CLAIMS>

        <CHECK_HINTS>
        Write concrete checks that could falsify this route, or none.
        </CHECK_HINTS>

        <RISK_FLAGS>
        Write unresolved mathematical risks, or none.
        </RISK_FLAGS>

        <FINAL_RESPONSE>
        {response_requirement}
        Keep it submission-ready and compact.
        </FINAL_RESPONSE>
        """
    ).strip()


def primary_prompt_v2(problem: str, contract: TaskContract) -> str:
    return dedent(
        f"""
        You are HORA-Math Blue Team Solver S1. Solve this low-risk mathematical problem with the
        shortest rigorous route. Use the assigned primary method family: {contract.primary_method}.
        Compute the answer before writing the protocol. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        {_strict_protocol_block(
            "Write the exact answer first, followed by a short derivation that checks sign, domain, and boundary conditions."
        )}
        """
    ).strip()


def blind_prompt_v2(problem: str, contract: TaskContract) -> str:
    response_requirement = (
        "The FINAL_RESPONSE field must contain a concise independent proof."
        if contract.requires_proof
        else "The FINAL_RESPONSE field must contain the exact answer and a short independent derivation."
    )
    return dedent(
        f"""
        You are HORA-Math Blue Team Solver S2, an ORTHOGONAL BLIND solver.
        You have not seen any other candidate. Solve the problem independently with the assigned
        method family: {contract.orthogonal_method}.

        Use a genuinely different route: definitions, construction, contradiction, an alternative
        representation, local calculation, counting, or another theorem family. State all needed
        assumptions. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        {_strict_protocol_block(response_requirement)}
        """
    ).strip()


def repair_prompt_v2(
    problem: str,
    contract: TaskContract,
    *,
    parent_answer: str,
    parent_response: str,
    challenge: str,
    witness: str,
    resolver_hint: str,
) -> str:
    response_requirement = (
        "Write the corrected conclusion and a concise complete proof addressing the challenge."
        if contract.requires_proof
        else "Write the corrected exact answer first and a short derivation that directly resolves the challenge."
    )
    return dedent(
        f"""
        You are HORA-Math Targeted Repair Solver. A red-team audit found a localized fatal defect.
        Recompute only the disputed point, preserve valid mathematics, and return a corrected
        submission. Do not defend a value merely because it appeared in the parent candidate.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        PARENT ANSWER
        {parent_answer}

        PARENT RESPONSE
        {parent_response[:2400]}

        RED-TEAM CHALLENGE
        challenge: {challenge or 'none'}
        witness: {witness or 'none'}
        resolver hint: {resolver_hint or 'none'}

        OUTPUT CONTRACT
        - Start immediately with <FINAL_CANDIDATE> and put the actual corrected mathematical answer
          inside it. Do not write analysis before the tag.
        - Do not copy instructions, placeholders, or the parent answer unless independently confirmed.
        - Emit the tags below in order and stop after </FINAL_RESPONSE>.

        <METHOD_FINGERPRINT>
        paradigm: choose one actual corrected method family
        representation: choose one actual representation
        theorem_family: write the actual theorem or method family, or none
        tool_channel: choose one of none|sympy|numeric|brute_force|residual|matrix
        interpretation_id: I1
        exposed_to_primary: true
        </METHOD_FINGERPRINT>

        <CRITICAL_CLAIMS>
        Write one to four actual corrected decisive claims using
        <CLAIM id="C1">a concrete mathematical statement</CLAIM>.
        </CRITICAL_CLAIMS>

        <CHALLENGE_RESOLUTION>
        State exactly why the red-team objection is resolved.
        </CHALLENGE_RESOLUTION>

        <CHECK_HINTS>
        Give one concrete falsification check, substitution, or theorem-condition check.
        </CHECK_HINTS>

        <RISK_FLAGS>
        Write remaining risks, or none.
        </RISK_FLAGS>

        <FINAL_RESPONSE>
        {response_requirement}
        </FINAL_RESPONSE>
        """
    ).strip()


def rescue_prompt_v2(problem: str, contract: TaskContract) -> str:
    response_requirement = (
        "Write a concise complete proof after the exact conclusion."
        if contract.requires_proof
        else "Write the exact answer and one decisive verification step."
    )
    return dedent(
        f"""
        You are HORA-Math Rescue Solver. All earlier candidates were invalid or unresolved.
        Recompute the problem from scratch using the shortest reliable route. Do not use any
        alleged previous answer. Do not use external online services.

        TASK CONTRACT
        {_contract_block(contract)}

        PROBLEM
        {problem}

        OUTPUT CONTRACT
        - Start immediately with <FINAL_CANDIDATE> containing the actual mathematical answer.
        - Do not emit analysis or Markdown before the first tag.
        - Do not copy placeholders such as "Exact answer" or "Minimal justification".
        - Stop after </FINAL_RESPONSE>.

        <METHOD_FINGERPRINT>
        paradigm: choose one actual method
        representation: choose one actual representation
        theorem_family: actual theorem or method family, or none
        tool_channel: choose one of none|sympy|numeric|brute_force|residual|matrix
        interpretation_id: I1
        exposed_to_primary: false
        </METHOD_FINGERPRINT>

        <CRITICAL_CLAIMS>
        Write one to four actual decisive claims using
        <CLAIM id="C1">a concrete mathematical statement</CLAIM>.
        </CRITICAL_CLAIMS>

        <CHECK_HINTS>
        Give one concrete independent check.
        </CHECK_HINTS>

        <RISK_FLAGS>
        Write remaining risks, or none.
        </RISK_FLAGS>

        <FINAL_RESPONSE>
        {response_requirement}
        </FINAL_RESPONSE>
        """
    ).strip()
