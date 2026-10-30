import hashlib
from pathlib import Path

import pytest

from rikishi.runtime_context import (
    CONTRADICTORY_BACKGROUND_SHA256,
    CONTRADICTORY_CORE_BINDINGS,
    background_statement_identity,
    recorded_negative_context,
)


@pytest.mark.parametrize("payload", [b"", b"\xff", b"not_tptp.", b"fof(a,axiom,p)."])
def test_supplied_background_must_match_its_raw_receipt(payload: bytes) -> None:
    result = recorded_negative_context(
        CONTRADICTORY_CORE_BINDINGS, [CONTRADICTORY_BACKGROUND_SHA256],
        background_bytes=[payload],
    )
    assert result == "unknown"


@pytest.mark.parametrize("payload", [b"", b"\xff", b"not_tptp.", b"fof(a,axiom,p)."])
def test_matching_raw_receipt_cannot_register_an_unobserved_background(payload: bytes) -> None:
    result = recorded_negative_context(
        CONTRADICTORY_CORE_BINDINGS, [hashlib.sha256(payload).hexdigest()],
        background_bytes=[payload],
    )
    assert result == "unknown"


@pytest.mark.parametrize("payloads", [[], [b"first", b"second"]])
def test_incomplete_background_bytes_never_fall_back_to_historical_hash(
    payloads: list[bytes],
) -> None:
    result = recorded_negative_context(
        CONTRADICTORY_CORE_BINDINGS, [CONTRADICTORY_BACKGROUND_SHA256],
        background_bytes=payloads,
    )
    assert result == "unknown"


@pytest.mark.parametrize("backgrounds", [[], [CONTRADICTORY_BACKGROUND_SHA256] * 2])
def test_structural_context_requires_exactly_one_recorded_background(
    backgrounds: list[str],
) -> None:
    result = recorded_negative_context(CONTRADICTORY_CORE_BINDINGS, backgrounds,
                                       background_bytes=[b"fof(a,axiom,p)."])
    assert result == "unknown"


def test_statement_identity_omits_only_standalone_layout() -> None:
    statements = b"fof(first,axiom,p).\nfof(second,axiom,q)."
    decorated = (b"% source path /old/location\n\nfof(first,axiom,p).\n"
                 b"/* a standalone annotation */\nfof(second,axiom,q).\n% end\n")
    result = background_statement_identity(decorated)
    assert result == (2, hashlib.sha256(statements).hexdigest())


@pytest.mark.parametrize("changed", [
    b"fof(renamed,axiom,p).\nfof(second,axiom,q).",
    b"fof(first,conjecture,p).\nfof(second,axiom,q).",
    b"fof(first,axiom,r).\nfof(second,axiom,q).",
    b"fof(first,axiom, p).\nfof(second,axiom,q).",
    b"fof(first,axiom,/* internal comment */p).\nfof(second,axiom,q).",
    b"fof(first,axiom,p,file('/original',first)).\nfof(second,axiom,q).",
    b"fof(second,axiom,q).\nfof(first,axiom,p).",
    b"fof(first,axiom,p).\nfof(second,axiom,q).\nfof(extra,axiom,p).",
    b"fof(first,axiom,p).",
    b"include('/different/location').\nfof(second,axiom,q).",
])
def test_statement_identity_binds_complete_statements_and_order(changed: bytes) -> None:
    expected = (2, hashlib.sha256(b"fof(first,axiom,p).\nfof(second,axiom,q).").hexdigest())
    result = background_statement_identity(changed)
    assert result != expected


@pytest.fixture(scope="module")
def installed_background(project_root: Path) -> tuple[bytes, bytes, bytes]:
    data = (project_root / ".rikishi/sigma/core/KBs/SUMO.tptp").read_bytes()
    first = data[data.index(b"fof("):data.index(b"\n", data.index(b"fof("))]
    second_start = data.index(b"fof(", data.index(first) + len(first))
    second = data[second_start:data.index(b"\n", second_start)]
    return data, first, second


@pytest.mark.integration
@pytest.mark.parametrize("change", [
    "standalone_comments", "inner_comment", "annotation", "role", "formula",
    "name", "order", "extra", "missing", "only_witness",
])
def test_installed_complete_background_context_rejects_structural_mutations(
    installed_background: tuple[bytes, bytes, bytes], project_root: Path, change: str,
) -> None:
    data, first, second = installed_background
    variants = {
        "standalone_comments": b"% relocated source\n/* changed layout */\n" + data,
        "inner_comment": data.replace(first, first.replace(b",axiom,", b",axiom,/* bound */"), 1),
        "annotation": data.replace(first, first[:-2] + b",file('/changed',original)).", 1),
        "role": data.replace(first, first.replace(b",axiom,", b",conjecture,"), 1),
        "formula": data.replace(first, first.replace(b"s__Set", b"s__ChangedSet"), 1),
        "name": data.replace(first, first.replace(b"kb_SUMO_1", b"renamed"), 1),
        "order": data.replace(first, b"ORDER_PLACEHOLDER", 1).replace(second, first, 1)
                     .replace(b"ORDER_PLACEHOLDER", second, 1),
        "extra": data + b"\nfof(extra,axiom,p).\n",
        "missing": data.replace(first, b"", 1),
        "only_witness": (project_root / "tests/runtime/fixtures/path-contradiction.p").read_bytes(),
    }
    payload = variants[change]
    result = recorded_negative_context(
        CONTRADICTORY_CORE_BINDINGS, [hashlib.sha256(payload).hexdigest()],
        background_bytes=[payload],
    )
    assert result == ("contradictory_translated_axioms_previously_observed"
                      if change == "standalone_comments" else "unknown")


@pytest.mark.integration
@pytest.mark.parametrize("key", list(CONTRADICTORY_CORE_BINDINGS))
@pytest.mark.parametrize("missing", [False, True])
def test_complete_background_cannot_override_missing_or_changed_provenance(
    installed_background: tuple[bytes, bytes, bytes], key: str, missing: bool,
) -> None:
    data = installed_background[0]
    provenance = dict(CONTRADICTORY_CORE_BINDINGS)
    if missing:
        del provenance[key]
    else:
        provenance[key] = "0" * 64
    result = recorded_negative_context(
        provenance, [hashlib.sha256(data).hexdigest()], background_bytes=[data],
    )
    assert result == "unknown"
