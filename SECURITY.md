# Security and sensitive evidence

Rikishi is a local research/operator workbench. Its dashboard binds to loopback;
the read-only Hypertext Transfer Protocol (HTTP) and Model Context Protocol (MCP) inspection interfaces are not an authenticated
multi-user service. Do not expose them publicly or treat read-only semantics as
a sandbox for untrusted archives, native executables or external source trees.

## Report privately

Email the maintainer privately at **danielarifriedman@gmail.com**, with
`Rikishi security report` in the subject. This is the contact listed on
[Daniel Ari Friedman's public GitHub profile](https://github.com/docxology).
Use the minimum information needed to arrange secure handling of sensitive
material. GitHub's **Report a vulnerability** route in the repository's Security
tab is an additional option when enabled. Do not put credentials, exploit
payloads, personal data or private research packets into a public issue.

The explicit email contact supplies the private reporting route required by the
release checklist. Its publication does not claim a tested email delivery, an
enabled GitHub reporting feature, a response deadline or a maintenance
service-level agreement.

Include the affected version or source commit, environment, bounded reproducer,
expected versus actual behavior, and the relevant file identities. Supply only
the minimum safe evidence. Rotate exposed credentials through their provider
and coordinate any sensitive-history remediation separately; do not rewrite
shared history as an unreviewed cleanup step.

## Handle research inputs carefully

- Keep downloaded runtimes, credentials, browser profiles, private audit trees
  and unreviewed raw logs outside public source/package assets.
- Verify the selected source/tool pins and independently supplied packet digests.
  A checksum obtained from the same untrusted packet does not authenticate it.
- Preserve failure evidence and reject unsafe paths, links, special files and
  changed provenance rather than silently falling back to cached outputs.
- Use fresh evidence destinations and correctly scoped repository admission.
  Stop only owned services/process groups through their supported lifecycle.
- Keep central processing unit (CPU)/wall limits, loopback boundaries and native control failures visible.
  An inconclusive prover status must not become an asserted proof.

Dependency and native-runtime licenses remain their owners' terms. The code's
MIT license does not grant rights to separately acquired inputs or exempt a
release from its public-payload review. See [release preparation](docs/release.md)
and [reproducibility](docs/reproducibility.md).

## Supported-version record

No public 1.0.0 release or maintenance window is claimed by this draft. Once a
release is published, record its supported version and security-reporting route
here as an explicit maintainer commitment. Do not infer ongoing support from a
development branch or an archived native-run receipt.
