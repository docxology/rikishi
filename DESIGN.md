# Rikishi design system

## 0. Scope

This contract describes the live corpus dashboard and portable corpus report.
The manuscript reader has its own full-width 12 mm publication policy, fixed
light paper, 17 px body text and 15 px code/secondary floor. See
[manuscript methods](docs/manuscript.md) and [current state](docs/current-state.md)
for that distinction and the exact saved verification scope.

## 1. Atmosphere and identity

A compact, white research workspace. Corpus measurements lead directly to exact
KIF evidence. A persistent document hierarchy makes corpus, term, and finite-model
tasks easy to find. There is no promotional hero. Notion's restrained typography
and hairline table structure inform the design; the user's white/neutral brief
overrides warm paper and decorative reference treatments.

## 2. Color

Tokens: paper/surface #ffffff, subtle #f6f7f9, ink #20242b, muted #596273,
line #dce0e6, accent #2459a8, wash #eef4ff, error #a32328.
Dark equivalents: paper #171a20, surface #1e232b, subtle #252b35,
ink #f0f3f8, muted #b5bfce, line #414b5c, accent #a6c8ff,
wash #263851, error #ffb4b7. Graph edges use the line token, selected nodes
the accent token. Charts use the same accent and show numerical labels.
Necessary control boundaries use a separate control-line token: #7b8594 light
and #8995a7 dark, with at least 3:1 contrast against adjacent theme surfaces.
Decorative panel and table rules retain the line token.
Every fresh page starts light, including a dark system preference. Dark mode is
an explicit session-only choice. No automatic media-query or stored override.

## 3. Typography

UI: system-ui, Helvetica Neue, Arial, sans-serif. Brand: Georgia, serif.
Code: system monospace. Sizes: title 32px (28px mobile), section 24px,
subhead 18px, body 16px, controls/secondary 14px, metadata 12px.
Measurements 28px, graph labels 12px. Line height 1.5; headings 1.2.
At widths up to 800px, body text is 17px and secondary, controls, metadata,
code and graph labels are at least 15px. The live workbench and portable corpus
report share these tokens. Result counts use the metadata token explicitly.

## 4. Spacing and layout

Base 4px; spacing 4,8,12,16,24,32,48px. Max width 1440px. Desktop columns
280px and remaining space, 24px gutter. Below 800px one column. Document
owns scroll, results alone have a bounded 420px scrolling region. All grid
children permit shrinkage; code wraps long source formulas.
Page gutters are 32px desktop and 16px phone; at 360px content remains usable.
Navigation wraps naturally. Tables use a keyboard-focusable horizontal scroll
region where all columns cannot fit, without horizontal page overflow. Table
regions are bounded at 560px vertically, with vertical boundary handoff to the
containing region or document. Taxonomy tables and degree charts use their
panel's vertical scroll owner rather than a nested vertical scroller.
The sticky header remains visible;
anchor offsets use its measured height plus 16px, including a third navigation
row at 360px. The initial fallback reserves 100px until measurement. Controls
wrap into a single column on phone. Queries use explicit submit/reset actions.
Ordinary web prose uses a 60ch maximum measure (within the 45–75ch target),
shrinking to the available column on smaller screens. Data tables, charts,
formula blocks and control groups retain their full available width.
Prose wraps unbroken provenance and source identifiers inside the available
column. Focus outlines sit inside focusable descendants of bounded scroll regions,
including recovery buttons, so containers cannot clip their top and sides.
Failed data views include an explicit reload
action and local-service recovery guidance.
Source disclosures have a 480px bounded scrolling region; accessible relationship
lists are bounded at 320px. Result buttons retain natural height inside their
420px scroll container rather than shrinking grid tracks.

## 5. Components

- Buttons: native button, neutral outline or ink fill, 44px minimum target;
  wash hover, pressed opacity, visible 2px focus outline. Disabled controls use
  the muted foreground and control-line boundary at full opacity, with a dashed
  border to distinguish their state without reducing text or edge contrast.
- Panels: semantic section, neutral hairline, 8px radius, 24px padding (16px phone).
- Workspace navigation: real anchor links, selected wash and aria-current;
  a visible checkmark accompanies the active workspace, independently of color.
  All workspace links reserve its 16px slot so route changes keep header height
  stable before navigation hands focus to a heading.
  User-initiated navigation hands focus to the target heading.
- Query tables: semantic caption/header/body, explicit sort and direction,
  server-side filter before paging; 44px row action/selection targets. Native
  checkbox selection applies to the displayed page. Copy/export names its exact
  selected row count; stale selection clears whenever query/page changes.
- Source inspector: exact indexed formula text, relative path, inclusive line
  range, hash/provenance and a pinned upstream link only for a clean revision.
- Status: loading with aria-busy, persistent live query population, visible
  empty/error/retry states; failed queries clear stale actionable rows.
- Results: full-width native buttons, term and formula count, selected wash;
  explicit Selected text follows aria-pressed, and selected relationship endpoints
  carry the same visible marker. Marker text is hidden from assistive technology
  where the control's existing ARIA state or name supplies that information.
  Separate empty and error messages; scrolling results remain keyboard reachable.
- Footer navigation: wrapping links with 44px minimum targets, 8px vertical and
  12px horizontal padding, and the existing 24px gaps.
- Standalone page/section heading links: 44px minimum targets with 8px vertical
  and 12px horizontal padding; inline prose links retain ordinary text flow.
- Graph: SVG edges and focusable linked node groups; click or Enter selects a
  term. Text alternatives list every visible relationship below the graph.
- Measures: semantic definition list, tabular numerals, no decorative icons.
- Source entries: details/summary, source path and line, wrapping preformatted KIF.
- Charts: labeled horizontal bars, numerical text available without color.
- Inference laboratory: a catalog of source-bound scenarios beside a replayed
  campaign table, with explicit prover, category and outcome filters. Each row
  opens its query, assumptions, source lines and recorded problem identity.
  Published results name the recorded digest and replay boundary; missing,
  invalid and offline evidence clear previous results. No browser control runs
  a prover. Existing panels, native controls and spacing tokens apply. The
  document owns scroll; the evidence table has its own labeled scroll region.

## 6. Motion and interaction

No decorative motion or scroll hijacking. Search submits explicitly and announces loading/results.
Initial hash navigation preserves the destination while ancestor data loads,
without moving focus. Preservation ends immediately on wheel, key, pointer, or
touch input, or when initial requests settle. Metrics reserve one 88px row on
desktop and two on phone, plus their existing padding/gaps. The FEP canvas reserves
200–512px by viewport width before its SVG loads. Evidence tables reserve 560px;
file and analytics loading regions reserve 640px and 240px respectively. These
slots remain readable and scrollable; data is never hidden to reduce layout shifts.
Async panes have permanent scroll slots: file distribution uses
`clamp(480px,75vh,800px)`; analytics and relation inventory use
`clamp(560px,80vh,900px)`; taxonomy uses `clamp(800px,110vh,1200px)`.
Term documentation reserves 180px desktop/240px phone; the direct diagram reserves
600px and the source notebook 480px. Status/provenance text reserves 63px desktop
and 126px phone (search/source summaries 42px/63px); FEP status reserves 84px.
All overflowing panes have names, keyboard focus, and native scrolling. These
stable instrument panes retain complete content and independent paging.
Graph navigation changes selection and source evidence together. Controls have
immediate hover/focus feedback. No positional animations require reduction.
Every finite-model request immediately clears the previous chart and metrics,
marks both regions busy, and announces the candidate probability being calculated.
Only the newest request may publish a result or clear busy state. Failed requests
leave empty data regions and explain how to retry by adjusting the slider after
the local service becomes available. Relation-inventory retries likewise replace
the previous error with a loading message and busy state. Integer path-budget
fields request a numeric keyboard; symbol and source-file fields keep text input.

## 7. Depth and surface

Neutral borders and tonal layers; no shadows, gradients or accent stripes.
Radius 8px for panels, 4px for controls. Graph lies on the subtle surface.

## 8. Accessibility constraints and accepted debt

Target WCAG 2.2 AA: visible keyboard focus, labeled controls, status live region,
semantic landmarks, 44px controls, responsive single column. Both themes use
explicit palettes. Graph data is duplicated as navigable text. Browser audit
results belong in the evidence directory; no Lighthouse score is presumed.
Personas: keyboard-only researcher following a measurement to its source;
screen-reader user inspecting row populations and exact formulas; phone user
filtering a corpus without page overflow. These are design requirements, not a
claim of complete accessibility certification. Actual screen-reader operation,
full keyboard traversal, physical-device behavior and other unverified scopes
remain explicit in the [current-state register](docs/current-state.md) and
[TODO](docs/TODO.md). Browser failures and unavailable audit tools must be
recorded without invented scores.

## 9. Publication reader

Layout: one full-width document flow with an in-flow table of contents;
the document owns vertical reading, and labeled table regions retain bounded
local horizontal/vertical traversal where complete mathematical objects require it.
The manuscript's explicit 12 mm/fixed-light policy remains separate from the
dashboard theme and prose-measure rules.

Publication non-policy spacing uses 4, 8, 12, 16 and 24 px tokens with a 4 px
radius. TOC targets retain at least 44 CSS px on both axes and 8 px separation.
Tables use available width and intentional cell wrapping rather than intrinsic
max-content widths. Short scientific-notation values remain atomic; long
identifiers remain breakable, and source/code/math content is preserved.
Any changed implementation must be checked against actual settled math and all
affected tables across phone and desktop configurations, not CSS strings alone.
