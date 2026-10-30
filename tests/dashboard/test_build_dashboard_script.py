import json
import subprocess
import sys
from pathlib import Path

from rikishi.ontology import OntologyIndex


def test_dashboard_import_has_no_effect_with_invalid_arguments(
    project_root: Path, tmp_path: Path,
) -> None:
    # Given a non-main import with arguments that the dashboard CLI rejects.
    script = project_root / "scripts/build_dashboard.py"
    probe = (
        "import runpy, sys; script = sys.argv[1]; "
        "sys.argv = [script, '--invalid-import-option']; "
        "runpy.run_path(script, run_name='maintenance_import_probe'); "
        "print('IMPORT_COMPLETED')"
    )
    # When a real Python subprocess imports the wrapper.
    result = subprocess.run(
        [sys.executable, "-c", probe, str(script)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False,
    )
    # Then argument parsing and report generation have not run.
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "IMPORT_COMPLETED\n"
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_dashboard_cli_exports_real_custom_index_and_output(
    project_root: Path, tmp_path: Path,
) -> None:
    # Given a real SQLite index whose source label includes markup.
    source = tmp_path / "<script>"
    source.mkdir()
    (source / "sample.kif").write_text(
        "(subclass Human Agent)\n(subclass Agent Entity)\n"
        '(documentation Human EnglishLanguage "A human agent.")\n',
        encoding="utf-8",
    )
    index = tmp_path / "custom-index.sqlite"
    OntologyIndex(index).build(source)
    output = tmp_path / "custom-output"
    # When the documented script runs with both custom paths.
    result = subprocess.run(
        [sys.executable, str(project_root / "scripts/build_dashboard.py"),
         "--index", str(index), "--output", str(output)],
        cwd=tmp_path, capture_output=True, text=True, timeout=60, check=True,
    )
    # Then all eight report outputs describe that index and remain offline.
    artifacts = json.loads(result.stdout)
    assert set(artifacts) == {
        "html", "data", "svg", "png", "analytics", "summary",
        "composition_svg", "composition_png",
    }
    assert {Path(path) for path in artifacts.values()} == set(output.iterdir())
    assert all(Path(path).parent == output for path in artifacts.values())
    assert all(Path(path).stat().st_size > 50 for path in artifacts.values())
    data = json.loads(Path(artifacts["data"]).read_text(encoding="utf-8"))
    analytics = json.loads(Path(artifacts["analytics"]).read_text(encoding="utf-8"))
    assert data["formulas"] == analytics["formula_denominator"] == 3
    assert data["files"] == analytics["indexed_files"] == 1
    assert analytics["unique_edges"] == 2
    html = Path(artifacts["html"]).read_text(encoding="utf-8")
    embedded = html.split('<script id="data" type="application/json">')[1].split("</script>")[0]
    assert "<script>" not in embedded
    assert "\\u003cscript>" in embedded
    assert json.loads(embedded)["source_root"] == str(source)
    assert 'src="http' not in html
    assert 'href="http' not in html
    assert "__DATA__" not in html
    assert Path(artifacts["png"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert Path(artifacts["composition_png"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert "<svg" in Path(artifacts["svg"]).read_text(encoding="utf-8")
    assert "<svg" in Path(artifacts["composition_svg"]).read_text(encoding="utf-8")
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / ".rikishi").exists()


def test_dashboard_cli_missing_index_fails_without_creating_outputs(
    project_root: Path, tmp_path: Path,
) -> None:
    # Given a missing custom index and a fresh output path.
    missing = tmp_path / "missing.sqlite"
    output = tmp_path / "report"
    # When the real CLI attempts to build a report.
    result = subprocess.run(
        [sys.executable, str(project_root / "scripts/build_dashboard.py"),
         "--index", str(missing), "--output", str(output)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False,
    )
    # Then failure is explicit and neither database nor report is manufactured.
    assert result.returncode != 0
    assert "FileNotFoundError" in result.stderr
    assert result.stdout == ""
    assert not missing.exists()
    assert not output.exists()
