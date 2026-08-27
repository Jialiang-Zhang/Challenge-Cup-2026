from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


RiskLevel = Literal["low", "medium", "high", "critical"]
EvidenceStatus = Literal["pass", "fail", "unknown", "not_applicable"]
EquivalenceStatus = Literal["equivalent", "not_equivalent", "unknown"]
ChallengeStatus = Literal[
    "open",
    "sustained",
    "rebutted",
    "resolved_by_tool",
    "not_applicable",
]


@dataclass(frozen=True)
class AgentConfig:
    """Runtime configuration for the HORA-Math orchestrator.

    The defaults intentionally keep the normal route to two model calls and the
    maximum conflict route to four.  The official runner can still clamp
    max_tokens or model calls independently.
    """

    primary_temperature: float = 0.2
    blind_temperature: float = 0.35
    audit_temperature: float = 0.0
    repair_temperature: float = 0.1

    primary_max_tokens: int = 4096
    blind_max_tokens: int = 3072
    audit_max_tokens: int = 1024
    repair_max_tokens: int = 2048

    max_model_calls: int = 4
    soft_deadline_seconds: float = 760.0
    finalization_reserve_seconds: float = 90.0

    # A genuinely independent second solution is the default.  This still cuts
    # the baseline from nine calls to two for ordinary questions.
    always_run_blind: bool = True
    red_team_for_medium: bool = False
    red_team_for_high: bool = True
    allow_repair: bool = True

    max_submit_chars: int = 6000
    max_candidate_context_chars: int = 3200


@dataclass(frozen=True)
class TaskContract:
    primary_domain: str
    secondary_domains: tuple[str, ...]
    problem_kind: str
    answer_schema: str
    requires_proof: bool
    requires_exact_answer: bool
    multipart_count: int
    risk_level: RiskLevel
    verification_modes: tuple[str, ...]
    mandatory_attacks: tuple[str, ...]
    likely_failure_modes: tuple[str, ...]
    route_hint: str
    primary_method: str
    orthogonal_method: str
    question_mode: str = "open_response"
    mode_confidence: float = 0.5
    alternate_modes: tuple[str, ...] = ()
    blank_count: int = 0
    choice_count: int | None = None
    answer_obligations: tuple[str, ...] = ("explicit_final_answer",)
    ambiguity_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class MethodFingerprint:
    paradigm: str = "unknown"
    representation: str = "unknown"
    theorem_family: str = "unknown"
    tool_channel: str = "none"
    interpretation_id: str = "I1"
    exposed_to_primary: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "paradigm": self.paradigm,
            "representation": self.representation,
            "theorem_family": self.theorem_family,
            "tool_channel": self.tool_channel,
            "interpretation_id": self.interpretation_id,
            "exposed_to_primary": self.exposed_to_primary,
        }


@dataclass
class ClaimRecord:
    claim_id: str
    statement: str
    dependencies: tuple[str, ...] = ()
    is_critical: bool = True
    status: str = "unverified"
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class SolutionCapsule:
    candidate_id: str
    source: str
    answer_raw: str
    final_response: str
    fingerprint: MethodFingerprint
    claims: list[ClaimRecord] = field(default_factory=list)
    check_hints: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    complete: bool = True
    truncated: bool = False
    response_chars: int = 0
    parse_warnings: tuple[str, ...] = ()
    parent_candidate_id: str | None = None
    challenge_resolution: str | None = None
    protocol_complete: bool = True
    recovery_source: str | None = None


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    candidate_id: str
    evidence_type: str
    status: EvidenceStatus
    strength: str
    checker: str
    target_claim_id: str | None = None
    detail_code: str | None = None


@dataclass
class Challenge:
    challenge_id: str
    candidate_id: str | None
    target_claim_id: str | None
    attack_type: str
    severity: str
    statement: str
    witness: str | None = None
    resolver_hint: str | None = None
    status: ChallengeStatus = "open"


@dataclass(frozen=True)
class AuditResult:
    verdict: str
    target_candidate_id: str | None
    target_claim_id: str | None
    attack_type: str
    severity: str
    challenge: str
    witness: str | None
    resolver_hint: str | None


@dataclass
class CandidateRecord:
    capsule: SolutionCapsule
    evidence_ids: list[str] = field(default_factory=list)
    challenge_ids: list[str] = field(default_factory=list)
    eligible: bool = True
    frozen: bool = False
    orthogonality_level: str = "O0"


@dataclass
class CaseState:
    contract: TaskContract
    candidates: dict[str, CandidateRecord] = field(default_factory=dict)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    challenges: list[Challenge] = field(default_factory=list)
    model_calls: int = 0
    tool_calls: int = 0
    repair_count: int = 0
    route: str = "R0"
    committed_candidate_id: str | None = None

    def add_candidate(self, capsule: SolutionCapsule) -> None:
        self.candidates[capsule.candidate_id] = CandidateRecord(capsule=capsule)

    def add_evidence(self, record: EvidenceRecord) -> None:
        self.evidence.append(record)
        candidate = self.candidates.get(record.candidate_id)
        if candidate is not None:
            candidate.evidence_ids.append(record.evidence_id)

    def add_challenge(self, challenge: Challenge) -> None:
        self.challenges.append(challenge)
        if challenge.candidate_id and challenge.candidate_id in self.candidates:
            self.candidates[challenge.candidate_id].challenge_ids.append(
                challenge.challenge_id
            )
