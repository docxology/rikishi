# Third-party materials and attribution

Rikishi's original operator code is MIT licensed; see [LICENSE](LICENSE).
That grant does not replace the terms of third-party sources, patches, styles,
fonts, dependencies or quoted material. The release artifact inventory must
identify what is actually redistributed.

## Material included in the source distribution

| Material | Location and retained identity | Terms and attribution |
| --- | --- | --- |
| Harvard citation style | `config/references.csl`, Secure Hash Algorithm 256-bit (SHA-256) `0ca3d2c7c881cd98cdd81098b5349f5921edf430498aa9a5a41918621cf7cc45` | The file names Patrick O'Brien and declares Creative Commons Attribution-ShareAlike 3.0. Preserve its original rights information. Its license applies to the style, rather than assigning that license to every generated manuscript. |
| Sigma compatibility patch | `config/patches/sigma-compound-type-guards.patch`, SHA-256 `184c6e055cd9cbb75950d3da1b5177f8efa95878ec917f54efd759a8f4f90889` | Applies to the separately pinned Sigma source. Sigma declares GPLv3. Preserve the upstream source and license identification with the patch; do not label upstream portions MIT. |
| Quoted Suggested Upper Merged Ontology (SUMO) expressions and source-derived examples | Referenced in the manuscript and source-bound study/report inputs | The pinned `Merge.kif` identifies the Institute of Electrical and Electronics Engineers (IEEE), copyright 2004, and requires acknowledgment of IEEE as source/copyright owner. The manuscript retains that acknowledgment. Other SUMO files may carry different notices; no blanket license is inferred for the whole corpus. |

The author has selected [CC BY 4.0 for the original manuscript and figures](LICENSE-PAPER.md).
The software remains MIT licensed. Neither grant replaces the separate terms
of quoted, reproduced or otherwise redistributed third-party material; preserve
its attribution and identify exceptions in the actual release inventory.

## Separately acquired dependencies

The complete SUMO corpus, Sigma installations, theorem-prover executables,
Java/toolchains, `fep_formal` checkout, Lean/mathlib caches, original alignment
workbook and browser/font caches are not supplied by installing Rikishi's wheel.
Source pins and acquisition methods are documented in
[installation](docs/installation.md), [runtime](docs/runtime.md),
[research](docs/research.md), and [manuscript methods](docs/manuscript.md).

- [Pinned SUMO source and its IEEE notice](https://github.com/ontologyportal/sumo/blob/efcd059f8feebfe3488a09f575f88d4d009b1e5c/Merge.kif).
- [Pinned Sigma license](https://github.com/ontologyportal/sigmakee/blob/d3cc7b43b38b0b45692291a1b33fe2b1a3de0095/LICENSE).
- [Citation Style Language repository](https://github.com/citation-style-language/styles/tree/ffd2a7b91280d84c9237ae97f9e5fd1f5abbe756).
- [Formalization source](https://github.com/ActiveInferenceInstitute/fep_formal).
- [Alignment precedent](https://doi.org/10.5281/zenodo.11463326).

Review the actual release package, embedded fonts and any optional evidence
attachments before redistribution. Retain each material's original notices and
do not bundle an authenticated/private cache merely because a local build used it.

## Historical scaffold in Git

The maintained source archives exclude `_template_resources/` and
`template_reference/`. Export rules do not hide the Git tree or its history.
Those historical copies retain these separate terms:

- The original `template_code_project` scaffold at
  `259125a197bce25e7d4fd8be7a466afa36678949` is MIT licensed, copyright
  Daniel Ari Friedman, 2026. See its
  [pinned license](https://github.com/docxology/template_code_project/blob/259125a197bce25e7d4fd8be7a466afa36678949/LICENSE)
  and the original attribution in [LICENSE](LICENSE).
- The copied rendering infrastructure records the `docxology/template` source
  revision `d160eb9c90eec18e365117c3ccaef731c47d8604`. Its
  [Apache 2.0 license](docs/licenses/template-Apache-2.0.txt) is preserved
  verbatim. Its bundled Kmyth subtree also retains its own `LICENSE` and
  `NOTICE`, including United States government contribution terms.
- The historical Liberation 2.1.5 font bodies retain their bundled
  `OFL.txt`, author attribution and provenance. They remain under the SIL Open
  Font License 1.1; Rikishi's MIT and manuscript CC BY grants do not relicense them.

Removing a scaffold from an exported archive does not remove its earlier
redistribution or authorize rewriting shared history.

## Fonts embedded in manuscript PDFs

The inspected manuscript embeds subsets of Latin Modern text and math fonts.
These font programs retain the GUST Font License, based on the LaTeX Project
Public License 1.3c or later. Keep the supplied
[text-font license](docs/licenses/latin-modern-GUST.txt),
[math-font license](docs/licenses/latin-modern-math-GUST.txt),
[text-font attribution](docs/licenses/latin-modern-README.txt) and
[math-font attribution](docs/licenses/latin-modern-math-README.txt)
with the manuscript deposit's notices. The original paper and figure license
does not relicense the embedded font programs. A changed renderer or font
selection requires inspection of that actual PDF and its corresponding notices.
