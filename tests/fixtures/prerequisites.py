"""Classify real installed-tool and retained-evidence prerequisites before selection."""

from __future__ import annotations

from typing import Final

import pytest

_SCOPED_FIXTURES: Final = (
    ("tests/manuscript/test_cache_replay.py", "packet"),
    ("tests/manuscript/test_native_manuscript.py", "saved_fresh_cache"),
    ("tests/runtime/test_fresh_cache.py", "experiment"),
    ("tests/manuscript/test_office_content.py", "package"),
)

_INSTALLED_TOOL_TESTS: Final = frozenset({
    ("tests/manuscript/test_office_content.py", "test_original_aligned_and_combining_negation_fail"),
    ("tests/manuscript/test_office_content.py", "test_no_tables_is_exact_identity"),
    ("tests/manuscript/test_office_content.py", "test_complete_shared_body_gathered_context_is_source_derived"),
    ("tests/manuscript/test_office_content.py", "test_context_display_operator_mutation_is_rejected"),
    ("tests/manuscript/test_office_layout.py", "test_native_reference_repairs_effective_link_and_caption_policy"),
    ("tests/manuscript/test_reading_policy.py", "test_pandoc_preserves_native_header_policy"),
    ("tests/manuscript/test_witness_abstracts.py", "test_percentage_width_does_not_force_a_distorting_html_height"),
    ("tests/manuscript/test_bridge_figures.py", "test_offline_template_script_syntax_with_rejecting_control"),
})


def prerequisite(path: str, name: str, fixtures: frozenset[str]) -> str | None:
    """Return the required native boundary for the resolved fixture closure."""
    if "bridge_packet" in fixtures:
        return "bridge_packet: native Lean/E/V campaign or authenticated retained packet"
    for scope, fixture in _SCOPED_FIXTURES:
        if path == scope and fixture in fixtures:
            return f"{fixture}: installed tools or authentic retained native evidence"
    if (path, name) in _INSTALLED_TOOL_TESTS:
        return "installed executable: real Pandoc or JavaScript syntax execution"
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Add integration markers before pytest applies -m; never discard tests."""
    for item in items:
        if not isinstance(item, pytest.Function):
            continue
        path = item.path.relative_to(config.rootpath).as_posix()
        reason = prerequisite(path, item.originalname or item.name, frozenset(item.fixturenames))
        if reason is not None:
            if item.get_closest_marker("integration") is None:
                item.add_marker(pytest.mark.integration)
            item.user_properties.append(("integration_prerequisite", reason))
