# 1.1.0 publication checklist

Use this checklist for **1.1.0** source and artifact qualification. The existing
[1.0.0 GitHub release](https://github.com/docxology/rikishi/releases/tag/v1.0.0)
is published and remains intact. These boxes apply only to the new candidate;
mark an item for its exact source and artifacts and retain the evidence locator.
See [release methods](docs/publication/release.md) and
[candidate notes](docs/publication/release-notes-1.1.0.md).

## Candidate and package

- [ ] Freeze the intended source commit and complete maintained-file inventory.
- [ ] Reconcile 1.1.0 across package/Python/server metadata, project lock entry,
  citation files, changelog, release notes and public guides.
- [ ] Confirm that `v1.1.0` does not conflict with an existing tag or release;
  preserve the published `v1.0.0`.
- [ ] Run the actual complete native `make check` for that source: every collected
  case, zero failures/errors/skips, unchanged 90% core and 60% infrastructure
  branch-inclusive floors, no excluded source lines, and package build success.
- [ ] Retain all warnings, failed attempts and rejecting controls with their
  actual source/runtime/command/exit bindings; do not relabel them after repair.
- [ ] Verify the wheel and source-distribution payloads, installation, command-line interface (CLI) and
  documented portable examples in a clean environment. Record platform scope.
- [ ] Check all distributed documentation targets independently of local output
  and private evidence trees; state actual native-platform prerequisites.

## Paper and reviewed artifacts

- [ ] Regenerate the paper from the selected source, bibliography, numerical
  inputs, separately verified campaigns and pinned renderer.
- [ ] Independently bind the actual Portable Document Format (PDF), source inputs, every figure and both
  placement axes; preserve complete mathematical and table content.
- [ ] Directly inspect every physical PDF page, with the cover on page 1 and the
  three ordered graphical abstracts on pages 2–4; inspect all figures/captions.
- [ ] Complete current independent reviews and retain their raw findings,
  dispositions and unverified limits. A previous build's acceptance is history.
- [ ] Assemble the review bundle with explicit file names, byte lengths, Secure Hash Algorithm 256-bit (SHA-256)
  digests, source identity, license scopes and a concise verification summary.
- [ ] Describe any supplied Word, Hypertext Markup Language (HTML) or figure/data supplements accurately;
  do not claim unoperated Word/physical-device/accessibility scenarios.

## Public exposure and rights

- [ ] Review the exact public source/package/asset allowlist and all Git history
  that would become public, including secrets, private research and dependencies.
- [ ] Exclude environments, native downloads/caches, browser profiles, private
  `.omo` trees, unreviewed raw packets and the original alignment workbook.
- [x] Record the author's license choice: [CC BY 4.0 for original manuscript text
  and figures](LICENSE-PAPER.md); code remains MIT and third-party terms remain separate.
- [ ] Verify that the actual PDF, figure supplements, package notices and deposit
  metadata carry those scopes; complete third-party attribution/conditions without
  silently relicensing upstream material.
- [ ] Verify that the release retains the explicit private security contact in
  [SECURITY.md](SECURITY.md).
- [ ] Record the actual remaining product/evidence limits and the maintainer's
  disposition; do not convert a literal departure into compliance.

## GitHub and Zenodo publication

- [ ] Bind the authorized ordinary push/tag/release and Zenodo publication
  actions to the concrete reviewed payload.
- [ ] Verify the actual public GitHub repository and approved tag/commit.
- [ ] Configure the correct Zenodo account/app access if using GitHub software
  archiving; keep `.zenodo.json` and `CITATION.cff` consistent.
- [ ] Create and verify the software release/archive, preserving its real digital object identifier (DOI).
- [ ] Upload and review the actual manuscript PDF record with accurate creators,
  resource type, description, license and preview selection.
- [ ] Cross-reference the software and manuscript using their actual identifiers.
  The precedent DOI `10.5281/zenodo.11463326` must not identify Rikishi.
- [ ] Independently download and compare the published files with the approved
  manifest; verify landing pages, version, license and public links.
- [ ] Update citation/release records with verified identifiers and publication
  dates, then publish the final release handoff with its stated limits.

Native execution, formal elaboration, source integrity, review, scientific
interpretation and publication remain separate claims. This checklist grants no
scientific, empirical, general Suggested Upper Merged Ontology (SUMO)-to-Lean preservation or release approval.
