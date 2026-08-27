from __future__ import annotations

import re
from dataclasses import dataclass

from .models import SolutionCapsule, TaskContract
from .task_profile import normalized_choice_letters


@dataclass(frozen=True)
class CoverageCheck:
    obligation: str
    status: str
    hard_failure: bool
    detail: str


def _multipart_markers(text: str) -> int:
    patterns = (
        r"(?:^|\n)\s*[（(](\d+|[一二三四五六七八九十]+)[)）]",
        r"(?:^|\n)\s*([a-zA-Z])[.)、]",
        r"[①②③④⑤⑥⑦⑧⑨⑩]",
    )
    values: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            values.add(match.group(1) if match.lastindex else match.group(0))
    return len(values)


def evaluate_answer_coverage(
    capsule: SolutionCapsule,
    contract: TaskContract,
) -> list[CoverageCheck]:
    answer = capsule.answer_raw.strip()
    response = capsule.final_response.strip()
    checks: list[CoverageCheck] = []

    for obligation in contract.answer_obligations:
        if obligation == "explicit_final_answer":
            checks.append(
                CoverageCheck(
                    obligation,
                    "pass" if answer else "fail",
                    not bool(answer),
                    "answer_present" if answer else "answer_missing",
                )
            )
            continue

        if obligation == "choice_letters":
            letters = normalized_choice_letters(answer)
            status = "pass" if letters else "fail"
            checks.append(
                CoverageCheck(
                    obligation,
                    status,
                    not bool(letters),
                    f"letters={''.join(letters) or 'none'}",
                )
            )
            continue

        if obligation.startswith("choice_count:"):
            expected = int(obligation.split(":", 1)[1])
            actual = len(normalized_choice_letters(answer))
            checks.append(
                CoverageCheck(
                    obligation,
                    "pass" if actual == expected else "fail",
                    actual != expected,
                    f"expected={expected};actual={actual}",
                )
            )
            continue

        if obligation.startswith("blank_count:"):
            expected = int(obligation.split(":", 1)[1])
            if expected == 1:
                ok = bool(answer)
                checks.append(
                    CoverageCheck(
                        obligation,
                        "pass" if ok else "fail",
                        not ok,
                        f"expected=1;answer_present={ok}",
                    )
                )
                continue

            labelled = len(
                re.findall(
                    r"(?:第\s*[一二三四五六七八九十\d]+\s*空|blank\s*\d+)\s*[:：=]",
                    answer,
                    flags=re.IGNORECASE,
                )
            )
            semicolon_parts = [item.strip() for item in re.split(r"[;；]", answer) if item.strip()]
            actual = labelled or (len(semicolon_parts) if len(semicolon_parts) > 1 else 0)
            if actual:
                checks.append(
                    CoverageCheck(
                        obligation,
                        "pass" if actual == expected else "fail",
                        actual != expected,
                        f"expected={expected};explicit_fields={actual}",
                    )
                )
            else:
                checks.append(
                    CoverageCheck(
                        obligation,
                        "unknown",
                        False,
                        f"expected={expected};field_boundaries_ambiguous",
                    )
                )
            continue

        if obligation == "binary_verdict":
            compact = re.sub(r"[\s。.!！]", "", answer).lower()
            allowed = {"正确", "错误", "对", "错", "true", "false", "yes", "no"}
            ok = compact in allowed
            checks.append(
                CoverageCheck(
                    obligation,
                    "pass" if ok else "fail",
                    not ok,
                    f"verdict={compact or 'none'}",
                )
            )
            continue

        if obligation.startswith("multipart_count:"):
            expected = int(obligation.split(":", 1)[1])
            marker_count = _multipart_markers(response)
            claim_count = len(capsule.claims)
            if marker_count >= expected:
                status, detail = "pass", f"markers={marker_count}"
            elif claim_count >= expected:
                status, detail = "pass", f"claims={claim_count}"
            else:
                status, detail = "unknown", f"markers={marker_count};claims={claim_count};expected={expected}"
            checks.append(CoverageCheck(obligation, status, False, detail))
            continue

        if obligation == "proof_chain":
            signals = re.findall(
                r"(?:therefore|hence|because|since|by |contradiction|由|因为|所以|故|从而|矛盾)",
                response,
                flags=re.IGNORECASE,
            )
            ok = len(response) >= 100 and bool(signals)
            checks.append(
                CoverageCheck(
                    obligation,
                    "pass" if ok else "unknown",
                    False,
                    f"chars={len(response)};reasoning_signals={len(signals)}",
                )
            )
            continue

        if obligation == "all_solutions":
            signal = bool(
                re.search(
                    r"(?:all solutions|only solutions|no other|所有解|全部解|仅有|除此之外无)",
                    response,
                    flags=re.IGNORECASE,
                )
            )
            checks.append(
                CoverageCheck(
                    obligation,
                    "pass" if signal else "unknown",
                    False,
                    (
                        "exhaustiveness_claim_present"
                        if signal
                        else "exhaustiveness_not_confirmed"
                    ),
                )
            )

    return checks
