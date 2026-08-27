from __future__ import annotations

import re

from .models import MethodFingerprint


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "unknown"


def orthogonality_level(a: MethodFingerprint, b: MethodFingerprint) -> str:
    if b.exposed_to_primary:
        return "O0"

    dimensions = (
        _normalized(a.paradigm) != _normalized(b.paradigm),
        _normalized(a.representation) != _normalized(b.representation),
        _normalized(a.theorem_family) != _normalized(b.theorem_family),
        _normalized(a.tool_channel) != _normalized(b.tool_channel),
        _normalized(a.interpretation_id) != _normalized(b.interpretation_id),
    )
    differences = sum(dimensions)

    if differences >= 3 and (
        a.tool_channel != b.tool_channel or a.theorem_family != b.theorem_family
    ):
        return "O3"
    if differences >= 2:
        return "O2"
    if differences == 1:
        return "O1"
    return "O0"


def is_independent_support(level: str) -> bool:
    return level in {"O2", "O3"}
