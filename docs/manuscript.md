# Reproduce the manuscript

The authored source is `manuscript/rikishi.md`. Run
`uv run rikishi report` then `uv run python scripts/render_manuscript.py` after environment setup. It computes
the numerical example, writes a figure and numerical JSON, then invokes the actual
docxology/template `PDFRenderer`, `WebRenderer`, and `render_docx` adapters.

The default renderer source repository is the sibling `../../Public/template`. Set
`RIKISHI_TEMPLATE_ROOT` to another complete template checkout when relocating.
The renderer exports committed `infrastructure/` and `pyproject.toml` at revision
`efce6d6f5b3c4e8e2bbf92d8250855a0a9389ae8` with `git archive`, then imports from the
verified snapshot under `.rikishi/template-renderer/<revision>/`. Existing snapshots
must match the archive file hashes; mismatches fail without overwriting them.
The original checkout's dirty files are neither imported nor modified.
The preserved `_template_resources/infrastructure` tree documents the inherited
template implementation but is not a complete installable template checkout.
Pandoc and a working XeLaTeX installation are required; missing dependencies are
errors rather than silently substituted renderers.

Artifacts are under `output/manuscript/`: `pdf/rikishi.pdf`, `docx/rikishi.docx`,
`web/manuscript__rikishi.html`, `fep-example.json`, `figures/fep-free-energy.png`, and
`render-receipt.json`. The receipt records renderer checkout revision, source hash,
artifact sizes and hashes, and the numerical result. Figures are copied into the
HTML edition's local figure directory so the file remains usable offline; MathJax
equation enhancement may require network access.

Renderer provenance includes the archive hash, original checkout cleanliness,
an explicit `template_worktree_used: false`, and hashes of every imported
infrastructure source module. `.rikishi/template-renderer/renderer-origin.json`
holds the complete archived-source manifest outside the snapshot. Revision lookup
uses the pinned origin rather than searching for a Git repository above the snapshot.

Corpus counts are hydrated from `output/data/corpus.json`; the report's
`output/corpus-files.png` is included as a second figure. The receipt records the
corpus export hash and substitutions, and retains the hydrated Markdown as an
artifact. See [reproducibility.md](reproducibility.md) for the input/output chain.

Inspect every PDF page using `pdftoppm`, open the HTML, and examine DOCX content
after generation. The receipt establishes which bytes were rendered, not scientific
validity or visual perfection. The document is a software methods manuscript and
clearly marks proposed FEP correspondences and verification limits.

## Importable methods and checks

`rikishi.manuscript.render_manuscript(root)` owns native adapter orchestration;
`rikishi.manuscript_provenance` owns typed corpus hydration, safe relative paths,
pinned Git snapshots, and artifact verification. The command scripts have no
import-time work. `rikishi.manuscript_verification.verify_manuscript(root)` performs
native PDF/DOCX/HTML inspection with explicit exceptions, including when Python
assertions are disabled. Source, corpus, bibliography, analytics, and output hashes
are checked so stale documents fail verification.

The additional `corpus-composition.png` shows formula-head composition and the
direct-edge degree distribution, including zero-degree symbols. Definitions and denominators are in
[metrics.md](metrics.md). Author-date linked citations render directly in every
edition; `references.bib` is copied alongside the outputs and included in the
receipt. [scholarship.md](scholarship.md) maps scientific claims to primary sources
and records source-inspection limits.

Run portable controls independently of the TeX installation:

```bash
source scripts/env.sh
uv run pytest tests/manuscript/test_manuscript_provenance.py
uv run rikishi report
uv run pytest tests/manuscript/test_native_manuscript.py
uv run python -O scripts/verification-manuscript.py
```

The native test regenerates all formats in the project output directory. It needs
the pinned renderer checkout, corpus exports, analytics, Pandoc, XeLaTeX, Poppler,
and the pinned sibling `fep_formal` checkout. Portable tests instead use real
temporary Git repositories and deliberately corrupted files. They do not substitute
for the native rendering test or visual review of every PDF page.
