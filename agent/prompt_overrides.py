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
