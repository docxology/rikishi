import hashlib
from collections.abc import Mapping, Sequence
from typing import Final

from rikishi.runtime_tptp import TPTPError, parse_tptp

CONTRADICTORY_CORE_BINDINGS = {
    "prover_sha256": "5c701155e35726eec787f4a864091791c5e554e8bc7bb4e6520fd0e6eada016a",
    "sigma_classes_sha256": "898c0f342c6868f1e6be3c3c9c95fed1e3565ef2143ca4a81f8524d16e3c6874",
    "sumo_lock_sha256": "0f8e785684de54ce36e1bc21c12f60a71e957fdc7d43cbb9bb3a410e0c85ac55",
    "profile_config_sha256": "35aa55c7495ec9e3915aa4be3382220ae70c7015269c5790de8d9425e69c2d7d",
}
CONTRADICTORY_BACKGROUND_SHA256 = "3af8bbb0023ce53c65b6504a025cc0f30ff2132667bbd1f8cd249e2e1967e3ed"
CONTRADICTORY_VAMPIRE_BINDINGS = dict(
    CONTRADICTORY_CORE_BINDINGS,
    prover_sha256="470529c41026e8f2844340e726bdc026406ced0b3afaaab72de7428456c84ec6",
)
CONTRADICTORY_STATEMENT_SHA256: Final = (
    "ab478bdfc42d614399c8e016a3bfbfc36f9a4578d029e8ac56bbf23144c959df"
)
CONTRADICTORY_STATEMENT_COUNT: Final = 36697
CONTEXT_FINGERPRINT_POLICY: Final = "tptp-statement-text-newline-join-v1"


def background_statement_identity(data: bytes) -> tuple[int, str]:
    statements = parse_tptp(data.decode("utf-8"))
    payload = "\n".join(statement.text for statement in statements).encode("utf-8")
    return len(statements), hashlib.sha256(payload).hexdigest()


def recorded_negative_context(
    provenance: Mapping[str, str], backgrounds: Sequence[str], *,
    background_bytes: Sequence[bytes] | None = None,
) -> str:
    if (len(backgrounds) != 1 or not any(
        all(provenance.get(key) == value for key, value in bindings.items())
        for bindings in (CONTRADICTORY_CORE_BINDINGS, CONTRADICTORY_VAMPIRE_BINDINGS)
    )):
        return "unknown"
    if background_bytes is None:
        matches = backgrounds[0] == CONTRADICTORY_BACKGROUND_SHA256
    else:
        if (len(background_bytes) != 1
                or hashlib.sha256(background_bytes[0]).hexdigest() != backgrounds[0]):
            return "unknown"
        try:
            matches = background_statement_identity(background_bytes[0]) == (
                CONTRADICTORY_STATEMENT_COUNT, CONTRADICTORY_STATEMENT_SHA256,
            )
        except (TPTPError, UnicodeDecodeError):
            return "unknown"
    if matches:
        return "contradictory_translated_axioms_previously_observed"
    return "unknown"
