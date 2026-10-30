# Review the manuscript and its evidence

A review bundle identifies one exact source candidate and one exact Portable Document Format (PDF). Its
manifest records each supplied file's byte length and Secure Hash Algorithm 256-bit (SHA-256) digest, the source
revision or complete source inventory, the renderer revision, and the applicable
verification results. A reviewer must be able to distinguish the current
candidate from the previous accepted build.

## Start with the bundle

1. Check the supplied manifest and PDF digest against the separately supplied
   review handoff. Rehashing a received file identifies its bytes; it does not
   independently authenticate its producer.
2. Read the scope and unresolved limitations before interpreting results. Keep
   incomplete native runs, warnings, access gaps and unverified surfaces visible.
3. Read the PDF as a complete document. Open every physical page at useful detail,
   including references, tables and continuations. Record the exact page and
   region for a finding; do not use a sampled contact sheet as complete coverage.
4. Compare the PDF to the retained source and data when evaluating a specific
   claim. A visually plausible number or equation is not a data join.

## Presentation checks

| Surface | Required review |
| --- | --- |
| Front matter | Cover on physical page 1; the three ordered graphical abstracts on physical pages 2–4; correct titles, summaries, affiliations and source labels. |
| Scientific content | Complete expressions, hypotheses, units and status distinctions; no lost signs, symbols, subscripts, cell values or source locators. |
| Figures | Every current figure and its caption, at the actual embedded size; no clipping, overlap, illegible labels or unintended image replacement. |
| Tables | Every row and column, including continuations; repeated headings and complete source/data labels. |
| Navigation | Contiguous section numbering, usable table of contents, correct destinations, readable Uniform Resource Locators (URLs) and resolved references. |
| Exported editions | Inspect the actual PDF and any claimed Word/LibreOffice or browser edition separately. One viewer does not qualify another. |

Nominal figure-text qualification joins the authored text sizes to the actual
embedded image bytes and both placement axes. The manuscript's figure floor is
7.5 pt. A source Scalable Vector Graphics (SVG) file, an unchanged pixel size, or a width-only calculation is
insufficient if a placement can compress height. This calculation does not
measure physical glyph height. The [visualization guide](visualizations.md) and
[manuscript methods](manuscript.md) describe the source and edition bindings.

For claimed web review, inspect all declared viewport/theme configurations,
document continuations and every locally scrolling table region. Verify actual
navigation targets at least 44 Cascading Style Sheets (CSS) px on both axes, the declared 17 px body and
15 px ordinary code/secondary-text floors, and the retained full-size figure
access. Treat expandable raster previews separately from ordinary web text.
Record actual target spacing rather than assuming a generic baseline is met.

## Interpret the evidence lanes

| Evidence | Permitted conclusion |
| --- | --- |
| Pinned Standard Upper Ontology Knowledge Interchange Format (SUO-KIF) excerpt and source span | That source contains the stated expression in its retained context. |
| Submitted automated theorem proving (ATP) problem and native controls | A result about the declared problem and encoding, with its actual execution status and background controls. |
| Exact finite calculation | An arithmetic result for the stated carrier, support and inputs. |
| Lean elaboration and axiom inventory | The named statements elaborated under the pinned hypotheses and retained trusted basis. |
| Shared identifiers across these lanes | The artifacts refer to the same authored witness; this alone establishes no general semantic-preservation theorem. |
| Seeded simulation | A reproducible simulation of its declared model, without empirical or biological validation. |

Trace claims through [scholarship](scholarship.md), [bridge methods](bridge-methods.md),
[inference methods](inference-methods.md), and [restricted semantic transport](semantic-transport.md).
Keep unsupported conjectures distinct from explicit refutations; timeouts and
resource exhaustion remain inconclusive. Do not infer whole-ontology consistency
from selected source kernels.

## Report a decision

A useful review states the exact artifact identity, pages/figures inspected,
directly observed findings, their severity, and the limits of the review. Keep
open departures open when accepting them with stated limits; do not mark literal
requirements compliant merely to satisfy an assembler. Preserve the original
finding and bind any correction to newly reviewed bytes.

Native Microsoft Word, physical print and phones, native large-text/200% zoom,
screen readers, full keyboard order, clipboard, initial-offline loading and
interactive failure states need their own operated evidence. Saved images,
accessibility trees and source inspection supply narrower observations.

The review-ready handoff supplies a current inspected document. Publication also
requires the [release checklist](../RELEASE_CHECKLIST.md), public-payload and
license review, final metadata, and an explicit release decision. Historical
local acceptance, a green test count or a visual verdict alone supplies none of
those additional decisions.
