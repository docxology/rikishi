# Rikishi design system

## 0. Research log

The embedded minimalist and Notion references inform the document-like typography,
neutral surfaces, compact controls, and visible source evidence. Linear and
Supabase were considered; editorial research navigation fits this task better.
The layout reference supplies a responsive sidebar/content grid with document
scroll ownership. Browser verification is owned by the integrating agent.
No external imagery or concept render is required for the measured graph surface.

## 1. Atmosphere and identity

A research notebook with an instrument panel. Warm paper and charcoal type make
the ontology legible; teal encodes graph relationships. The signature is a live
relationship map beside the exact KIF source supporting each selected term.

## 2. Color

Tokens: paper #f6f5f0, surface #ffffff, ink #252a28, muted #626960,
line #dedfd7, accent #176b62, wash #e7f0e9, error #a12d26.
Dark equivalents: #171c1a, #202723, #eef0e9, #b3bdb4, #3e4941,
#8ed3bf, #293d32, #ffb3aa. Graph edges use the line token, selected nodes
the accent token. Charts use the same accent and show numerical labels.

## 3. Typography

UI: Helvetica Neue, Arial, sans-serif. Editorial title: Georgia, serif.
Code: system monospace. Sizes: title clamp(36px,5vw,64px), section 24px,
subhead 18px, body 16px, secondary 14px, metadata 12px. Line height 1.5.

## 4. Spacing and layout

Base 4px; spacing 8,12,16,24,32,48px. Max width 1440px. Desktop columns
320px and remaining space, 24px gutter. Below 800px one column. Document
owns scroll, results alone have a bounded 420px scrolling region. All grid
children permit shrinkage; code wraps long source formulas.
Source disclosures have a 480px bounded scrolling region; accessible relationship
lists are bounded at 320px. Result buttons retain natural height inside their
420px scroll container rather than shrinking grid tracks.

## 5. Components

- Buttons: native button, neutral outline or ink fill, 44px minimum target;
  wash hover, pressed opacity, visible 2px focus outline, disabled opacity.
- Panels: semantic section, neutral hairline, 8px radius, 24px padding.
- Results: full-width native buttons, term and formula count, selected wash;
  separate empty and error messages; scrolling results remain keyboard reachable.
- Graph: SVG edges and focusable linked node groups; click or Enter selects a
  term. Text alternatives list every visible relationship below the graph.
- Measures: semantic definition list, tabular numerals, no decorative icons.
- Source entries: details/summary, source path and line, wrapping preformatted KIF.
- Charts: labeled horizontal bars, numerical text available without color.

## 6. Motion and interaction

No decorative motion. Search submits explicitly and announces loading/results.
Graph navigation changes selection and source evidence together. Controls have
immediate hover/focus feedback. No positional animations require reduction.

## 7. Depth and surface

Neutral borders and tonal layers; no shadows, gradients or accent stripes.
Radius 8px for panels, 4px for controls. Graph lies on the paper surface.

## 8. Accessibility constraints and accepted debt

Target WCAG 2.2 AA: visible keyboard focus, labeled controls, status live region,
semantic landmarks, 44px controls, responsive single column. Both themes use
explicit palettes. Graph data is duplicated as navigable text. Browser audit
results belong in the evidence directory; no Lighthouse score is presumed.
