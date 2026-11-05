# Versioned GitHub and Zenodo releases

Rikishi publishes an exact source/tag release on GitHub and two distinct Zenodo
records: software and a software-methods preprint. Each release binds the
reviewed source, package files, manuscript editions and public verification
summary to their actual hashes. A reserved digital object identifier (DOI)
supports the final manuscript render; publication and retrieved-file parity
must subsequently be verified.

The existing [v1.0.0 GitHub release](https://github.com/docxology/rikishi/releases/tag/v1.0.0)
remains intact. Use the [1.1.0 checklist](../../RELEASE_CHECKLIST.md),
[candidate notes](release-notes-1.1.0.md) and [review guide](review.md) for the
new version. This guide follows the canonical
[`docxology/template` publication runbook](https://github.com/docxology/template/blob/50ee012974466c230bfd0d23dbece6556c89cf36/docs/guides/publication-runbook.md)
and its [concept/version DOI policy](https://github.com/docxology/template/blob/50ee012974466c230bfd0d23dbece6556c89cf36/docs/guides/zenodo-doi-strategy.md),
using its public Zenodo application programming interface (API) client for
Rikishi's recorded deposition identifiers.

## Keep the two publication identities separate

The 1.1.0 reservation step established the following identities. The draft
identifiers are operational handles for that initial upload. Verify completed
publication using the public records and release receipt; a reservation alone
does not establish registration or file publication.

| Object | Draft ID | Concept identity | Immutable version identity | Required resource type and rights |
| --- | --- | --- | --- | --- |
| Software | `23987623` | `10.5281/zenodo.23987622` | `10.5281/zenodo.23987623` | `upload_type=software`; MIT License for original software, with manuscript and third-party exceptions retained. |
| Manuscript | `23987671` | `10.5281/zenodo.23987670` | `10.5281/zenodo.23987671` | `upload_type=publication`, `publication_type=preprint`; Creative Commons Attribution 4.0 International (CC BY 4.0) for original manuscript text and figures. |

The authenticated draft observations returned the draft/version identities and
concept record IDs. Template's parser obtains the concept DOI from the returned
concept record ID when an explicit concept DOI field is absent. Retain that
distinction in reservation evidence and verify both identifiers again against
the published resources.

The manuscript's identity fields belong in
[`config/manuscript.yaml`](../../config/manuscript.yaml):

```yaml
publication:
  doi: "10.5281/zenodo.23987670"
  version_doi: "10.5281/zenodo.23987671"
  version_record: "https://zenodo.org/records/23987671"
  software_version_doi: "10.5281/zenodo.23987623"
```

`doi` identifies the manuscript series; `version_doi` and `version_record`
identify this manuscript edition. `software_version_doi` links the separate
software version. These fields must not be exchanged. Software citation
sidecars describe the software series and version: their software concept
identity is `10.5281/zenodo.23987622`, not the manuscript concept DOI.
Keep `CITATION.cff`, `.zenodo.json`, package version, release notes and the
actual deposit metadata consistent for their respective objects.

The alignment precedent `10.5281/zenodo.11463326` identifies another work.
It is not a Rikishi identifier. Likewise, draft metadata and reservation dates
must not be described as a completed publication; use the actual publication
day when one is recorded.

## Freeze and qualify one candidate

Finish the intended source, documentation, publication identities and metadata
before freezing the candidate commit. Reconcile package/Python/server version
exports, the lockfile's project entry, study authorities and citation files.
A changed lock or study authority can require new portable inputs and campaign
evidence; follow the [dependency-provenance contract](../research/research.md#dependency-provenance-revisions).
Preserve earlier receipts with their actual source identities.

Complete the actual `make check` obligations for that source: skill projection,
lint, static types, every native test, the unchanged branch-inclusive coverage
floors of 90% core and 60% infrastructure, and package builds. Where the managed
runner requires bounded partitions or a separately qualified project workflow,
retain an exhaustive common-source inventory and aggregate the actual outcomes.
No case can be silently omitted, skipped or waived to obtain a release pass.
Verify the built wheel and source distribution in a fresh consumer environment.
Keep failures, warnings and rejecting controls as evidence.

Finish native qualification before producing the final edition: some native
tests deliberately regenerate canonical verification or rendering outputs.
Then reconcile the final producer reports and custody, perform the required
fresh formal verification, render the DOI-bearing editions through the pinned
canonical template, and verify the actual output. Independently inspect every
physical Portable Document Format (PDF) page, all figures/captions and the
manuscript's numerical and scientific claims. Freeze those exact edition bytes
before publication. A subsequent source edit or artifact regeneration requires
the affected qualification and review again.

Use the correct mounted runtime and governed repository operations described
in [contributing](../../CONTRIBUTING.md). Expensive checks belong in their
qualified bounded execution context; short publication leases protect the
final source/tag and external mutations.

## Curate an explicit public asset set

Prepare an allowlist with each asset's name, byte length, Secure Hash Algorithm
256-bit (SHA-256) digest, source identity, destination and license scope.
Review current source and any history becoming public. Keep the actual code
license, manuscript license and reviewed third-party notices in the payload.

| Destination | Intended payload |
| --- | --- |
| GitHub `v1.1.0` | Exact reviewed tag/commit and the approved source, package, manuscript and verification assets. |
| Zenodo software record | The approved source archive, source distribution and wheel, with their rights/notices. |
| Zenodo manuscript record | The final reviewed PDF, approved manuscript bundle/supplements and honest verification summary. |

Include optional Word or Hypertext Markup Language (HTML) editions only when
their actual files and qualification scope are described. Preserve the final
edition's embedded-font inventory and required font notices. Inspect the
actual PDF with `pdffonts`; a previous edition's inventory is not evidence for
new bytes.

Upload individual allowlisted files. Do not recursively upload generated
output, native capture directories, logs, environments, caches, credentials,
browser profiles or the separately acquired alignment workbook. Public
reproduction instructions must work from source acquisition recipes, pins and
public locators rather than private retained evidence. The
[third-party inventory](../../THIRD_PARTY_NOTICES.md) and
[manuscript license](../../LICENSE-PAPER.md) identify rights that survive
packaging. A software record's MIT license does not relicense manuscript
sources or third-party material inside its archive.

## Resume recorded drafts through template's public client

Use the verified canonical template checkout with a qualified runtime carrying
the client's actual dependencies. Bind
the actual imported template source/version in the publication receipt.
Rikishi is a standalone repository with `config/manuscript.yaml`; template's
project release command-line interface (CLI) expects its own project layout
and does not accept these existing draft IDs. Reuse the public client directly
with the two approved IDs instead of creating another template project or
another deposition.

The following fragment performs only the two authenticated reads. Run it from
the verified template root, using the approved explicit credential source:

```python
import os
from pathlib import Path

from infrastructure.core.credentials import ensure_dotenv_loaded
from infrastructure.publishing.zenodo import ZenodoClient, ZenodoConfig

ensure_dotenv_loaded(Path.cwd() / ".env")
token = os.environ.get("ZENODO_PROD_TOKEN") or os.environ.get("ZENODO_TOKEN")
if not token:
    raise RuntimeError("Production Zenodo credential unavailable")
client = ZenodoClient(ZenodoConfig(access_token=token, sandbox=False))
software = client.get_deposition("23987623")
manuscript = client.get_deposition("23987671")
```

The explicit loader preserves an already selected environment value. Keep
credentials in memory and Bearer headers; exclude them from command arguments,
saved reports and links. Retain credential-free observations of the returned
IDs, owner, submission/state, metadata, DOI fields and files. Require the
expected account and unpublished draft state before mutation. A failed read
must remain a failure against that draft, rather than triggering a replacement.

After the concrete source/artifact/metadata checks are complete, the client's
existing operations are:

| Operation | Public method | Required comparison |
| --- | --- | --- |
| Parse the actual draft response | `DepositionResult.from_zenodo_body(body)` | Exact draft ID, reserved identifiers and returned secure Zenodo bucket. |
| Update approved metadata | `client.update_deposition_metadata(id, metadata)` | Pass the nested `metadata` object from the reviewed JavaScript Object Notation (JSON) metadata; preserve software/preprint types and identifiers. |
| Upload one approved file | `client.upload_file(bucket, file, object_key=file.name)` | Exact approved name, length and digest before sending. |
| Publish the exact draft | `client.publish(id)` | Returned identifier agrees with the reserved version DOI; independently retrieve the published state and files. |

Use `DepositionResult` from `infrastructure.publishing.zenodo`. Validate that
the returned bucket is secure `zenodo.org` storage under `/api/files/` before
using it. Generate metadata from the final title, abstract, author/affiliation
and researcher identifier fields; retain separate software and preprint
resource types and reciprocal related identifiers. Re-read after metadata
updates and require the reserved identities unchanged.

For an existing file, compare the exact name, size and service checksum, then
download it and independently compare SHA-256 before skipping an upload.
A mismatch requires review. Preserve previous files and partial outcomes;
do not clear or replace an existing draft inventory automatically. Before
publication, require the complete remote inventory to equal the approved
destination subset and verify every remote file's bytes.

For later releases in a published series, use template's actual
`create_new_version` method against the verified previous deposition, then
retrieve the new draft and its returned identifiers. Keep the concept DOI
stable and render the new immutable version identity. For the initial 1.1.0
release, resume the recorded reservations. Once they are published, use the
new-version operation for a later release.

## Publish GitHub through its admitted write path

The GitHub tag must identify the exact qualified commit. Confirm that
`v1.1.0` and the release do not conflict with an existing publication; preserve
`v1.0.0`, unrelated work and ordinary shared history. Use an ordinary admitted
push and reverify the remote commit/tag.

In the managed vault, GitHub writes require the mapped owner token, the
selected enabled write class, a current frozen plan and its exact application
confirmation under idle-writer admission and short repository leases. Ambient
`gh` login and a template convenience helper do not replace that admission.
Do not edit tracked vault configuration to enable a write class.

Prepare the release as a draft at the exact tag, attach every manifest-bound
asset, and retrieve/verify their names, lengths and bytes before publishing
the GitHub release. A helper that publishes the release before attaching or
verifying assets does not implement this ordering. Re-read the published
release and all its assets after the final state change.

## Verify the completed publication

Require both Zenodo depositions to be submitted/published and their public
records to expose version `1.1.0`, the expected resource types, creators,
licenses, identifiers and exact files. Download every published artifact and
compare SHA-256 with the approved local manifest. The manuscript PDF retrieved
from GitHub and Zenodo must have the same final bytes. Check the actual
landing pages, version DOI links, concept DOI links and cross-references.
An upload response or DOI string alone does not establish this parity.

Retain the exact commit/tag, source and asset manifest, reservation and
publication observations, test/coverage/package results, edition review,
independent-review dispositions, rights decisions, authorization and verified
public links. Publish a credential-free handoff describing the actual remaining
scientific, proof-authentication, platform and document-operation limits.
Archive hashes belong in the asset manifest and release receipt; do not create
a self-referential archive hash by modifying its own contents after freezing.

The official [Zenodo API documentation](https://developers.zenodo.org/),
[file guidance](https://help.zenodo.org/docs/deposit/manage-files/) and
[license guidance](https://help.zenodo.org/docs/deposit/describe-records/licenses/)
describe the service contract. Publication records what was supplied and
verified; it does not turn bounded experiments into general ontology theorems
or empirical validation.
