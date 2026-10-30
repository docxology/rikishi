# Prepare the GitHub and Zenodo release

The proposed first public version is **1.0.0**. This guide describes preparation;
it does not report that a tag, public repository, digital object identifier (DOI) or Zenodo record exists.
Use the [release checklist](../RELEASE_CHECKLIST.md) as the concrete decision
record and the [review guide](review.md) for the manuscript artifact.

## Freeze one release candidate

Finish the intended source and documentation changes before the release freeze.
Keep the package metadata, Python version export, server metadata, lockfile's
project record, `CITATION.cff`, any `.zenodo.json`, changelog and release notes
consistent. Do not add an invented publication date or DOI. Record the exact
candidate commit and complete file hashes, then qualify that candidate.

Also reconcile the packaged alignment and shared-witness study dependency pins
with the exact changed lock bytes. A software-version edit alone can invalidate
these authorities. Run the release-authority preflights before native work; the
[research contract](research.md#dependency-provenance-revisions) distinguishes a
provenance-only revision from a changed scientific study. Preserve old receipts,
acquire a new portable-input bundle, regenerate affected campaigns and render new
editions with their actual provenance. Never rehash old reports as new executions
or reuse an obsolete portable receipt after changing its authority.

Run applicable regression and rejecting controls, the complete native
`make check`, both branch-inclusive coverage floors (90% core, 60%
infrastructure), and the package build. A fail-fast run can establish a RED
result; a successful release gate must include every collected case with no
failures, errors or skips. Preserve warnings and earlier failures. Qualify the
wheel and source distribution in a clean environment and inspect their actual
payloads. A previous source candidate's pass does not qualify a new version.

Use fresh external test roots, the correct project runtime and a supported
Rikishi repository lease; see [contributing](../CONTRIBUTING.md). Do not wait for
an unrelated repository's full test suite. Do not alter source while its frozen
native qualification is running.

## Review the public payload

Prepare an explicit allowlist for source and release assets. Audit both the
intended current payload and any Git history that will become public. Ignoring a
path now does not remove an earlier committed secret or private artifact.

Exclude development environments, downloaded native runtimes, browser profiles,
credentials, private `.omo` evidence, unreviewed raw runtime packets, and the
separately acquired alignment workbook. Include the actual code license and
reviewed third-party notices; do not relabel upstream material as MIT. Keep the
source acquisition recipe, pins, public source locators and reproducibility
instructions available without requiring private evidence trees.

For the review/release bundle, bind the actual Portable Document Format (PDF), optional Word/Hypertext Markup Language (HTML) editions,
source/package archives, selected public data and figure supplements, and an
honest verification summary. Record names, lengths, Secure Hash Algorithm 256-bit (SHA-256) digests and license
scope. Do not publish all ignored output merely because it exists. Review the
rights and sensitive content of each included supplement.

The author has selected [CC BY 4.0 for the original manuscript and figures](../LICENSE-PAPER.md).
Code and the software archive remain MIT licensed; `.zenodo.json` and
`CITATION.cff` describe that software record. Select `cc-by-4.0` for the separate
manuscript deposit and retain the manuscript/figure notice with figure supplements.
Preserve all third-party conditions and identify exceptions in the file inventory.
The selected record license must accurately describe the supplied files; see
[Zenodo's license guidance](https://help.zenodo.org/docs/deposit/describe-records/licenses/).

## Keep software and manuscript records distinct

| Object | Prepared identity and review |
| --- | --- |
| GitHub source release | Approved `v1.0.0` tag at the exact reviewed commit; code/package metadata and changelog agree. |
| Zenodo software archive | Archive of that GitHub release, or a separately reviewed manual software upload; verify the resulting record and its DOI. |
| Zenodo manuscript | Actual inspected PDF with its own accurate resource type, title, creators, license, files and identifier. |

The software integration does not by itself prove that the manuscript PDF was
uploaded. Attach or upload the intended PDF deliberately, and verify the actual
record file list and downloaded bytes. Link the software and paper records using
their real identifiers only after those identifiers exist.

`10.5281/zenodo.11463326` identifies the alignment precedent cited by the paper.
It is not a Rikishi DOI and must not be reused as one.

Zenodo can read `CITATION.cff` for GitHub archives. If `.zenodo.json` is also
present, Zenodo uses that file instead, so validate both against the same
approved metadata. Keep absent identifiers absent rather than inserting dummy
DOIs. [Zenodo metadata documentation](https://help.zenodo.org/docs/github/describe-software/zenodo-json/)
describes this precedence.

## Final publication steps

Perform these effects only after the exact release payload and remaining limits
have been reviewed and publication explicitly authorized:

1. Verify the final source revision, ordinary push target and absence of an
   existing conflicting `v1.0.0` tag. Preserve unrelated work; do not force-push or
   rewrite shared history.
2. Complete any approved public-visibility change only after the history and
   payload exposure review. Configure the intended private security-reporting
   route. The GitHub–Zenodo integration requires a public repository, and an
   organization may need to approve the Zenodo app's access.
3. Enable the selected GitHub repository in the correct Zenodo account, if using
   the software integration. Create the approved GitHub release from the exact
   tag and attach only the manifest-bound assets.
4. Wait for Zenodo processing, inspect any reported errors, and verify the
   software record's version, creators, license, source link and actual files.
   Separately review and publish the prepared manuscript record as intended.
5. Download the published PDF and archives, independently compare their bytes
   with the approved manifest, and confirm that every claimed public Uniform Resource Locator (URL)/DOI
   resolves. Record the identifiers in the repository and citation metadata
   through a separately reviewed follow-up; avoid a self-referential archive hash.

The operational steps follow [GitHub's citation guidance](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content)
and [Zenodo's release-archive guidance](https://help.zenodo.org/docs/github/archive-software/github-upload/).
Neither draft metadata nor successful upload initiation establishes publication.

For the PDF record, select the reviewed PDF as the preview file and check the
landing page. Prefer open formats and remove incidental `.DS_Store`, `__MACOSX`
and equivalent packaging debris from new distributable archives, while retaining
the original research evidence separately. See [Zenodo file preparation](https://help.zenodo.org/docs/deposit/manage-files/).

## Required release record

Retain the candidate commit/tag, source and asset manifest, actual test/coverage
and package results, all-page PDF review, independent review dispositions,
public-payload/history and license decisions, final publication authorization,
and the verified public URLs and identifiers. State unverified native, physical,
scientific and proof-authentication scopes explicitly. Publication does not turn
those limits into successful experiments or general ontology theorems.
