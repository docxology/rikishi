# Install and choose a workflow

Use the source and lockfile for the version you are reviewing. The 1.0.0 files
are release preparation until the release checklist records the actual tagged
commit and published assets. No PyPI installation is promised by this guide.

## Portable methods from a source checkout

Rikishi requires Python 3.12 or newer; development and the current workstation
qualification use Python 3.12. Use [uv](https://docs.astral.sh/uv/) and the
repository's committed `uv.lock` rather than independently upgrading dependencies.
From an authorized source checkout or an extracted source distribution:

```bash
uv sync --locked
uv run --locked --no-sync rikishi --help
uv run --locked --no-sync rikishi fep-demo
uv run --locked --no-sync rikishi active-demo
uv run --locked --no-sync rikishi fep-evaluate examples/fep-log-model.json --logarithmic
```

These finite calculations do not install Sigma, run an automated theorem prover,
or compile Lean. Their inputs and numerical conventions are described in
[finite methods](fep.md), [one-step planning](active-inference.md),
[bridge methods](bridge-methods.md), and the
[Python interfaces](API.md). Source installation alone supplies no native-runtime
or cross-platform qualification result.

For portable tests, first acquire the public source inputs with the declared
hash checks. The alignment workbook is downloaded separately, not bundled:

```bash
uv run --locked --no-sync python scripts/prepare_portable_inputs.py --help
```

Follow [testing](testing.md) for the actual acquisition and selectors. Allocate a
new external `--basetemp` for every test run. Do not let a review run prune a
shared directory containing another run's retained evidence.

## External publication caches

For source work on the managed GitVault workstation, `source scripts/env.sh`
binds `TEXMFVAR`, `TEXMFCONFIG` and `TEXMFCACHE` to the external Rikishi cache
root, alongside Python, plotting and temporary-file caches. This prevents
publication tools from writing their user caches/configuration under the internal
home directory. Existing internal files are preserved; the installed TeX
distribution and any user package library remain read-only inputs. Check the
actual bindings with `kpsewhich -var-value=TEXMFVAR` (and the other two names)
before native rendering. An environment declaration alone is not path verification.

## Static types and the pinned renderer source

The full type gate imports interfaces from the exact pinned renderer source,
even though a portable numerical calculation does not render a document.
An isolated source-only type check without that source reports missing-module
warnings and fails; those warnings must not be suppressed.

For a source checkout, acquire the public template repository and use the
existing archive-and-hash verifier to prepare its exact selected revision:

~~~bash
git clone https://github.com/docxology/template.git .rikishi/template-source
uv run --locked --no-sync python - <<'PY'
from pathlib import Path
from rikishi.manuscript_provenance import prepare_renderer
prepare_renderer(Path.cwd(), Path(".rikishi/template-source"))
PY
uv run --locked --no-sync basedpyright
~~~

Use a new destination for the clone, or an independently verified existing
template checkout. This preparation reads a pinned Git archive and verifies its
source files; it does not launch a renderer, install Sigma or prove a theorem.
The portable GitHub workflow checks out the same full renderer revision and calls
the same preparation method before the type gate. Its declaration still needs
an actual hosted run before claiming hosted-CI success.

## Native workstation workflow

The current native bootstrap enforces a mounted external workspace and a
checkout beneath it. The supplied environment script expects the GitVault
`Username/` layout. Automatic native provisioning targets Apple Silicon macOS;
other hosts require an externally installed Java runtime and further native
prerequisite preparation. This is a concrete support boundary, not a tested
general Linux/Windows installer.

On the configured workstation, from the canonical checkout:

```bash
source scripts/env.sh
uv sync --locked
uv run --locked --no-sync python -B -c 'import sys; print(sys.prefix); print(sys.base_prefix)'
```

Both Python prefixes must resolve onto the mounted workspace. An external
virtual environment can still depend on an internal base interpreter. Keep uv,
Matplotlib and temporary storage external, and retain `UV_LINK_MODE=copy` when
uv crosses filesystems. Do not create a replacement local checkout when the
external volume is absent.

GitVault operators run project mutations and gates under the supported
`with-repo docxology/rikishi` repository admission, as described in
[contributing](../CONTRIBUTING.md). The same repository and shared Git store
serialize; unrelated repository leases remain compatible. A different project's
tests are not a prerequisite for Rikishi. Genuine collection-wide deployment,
configuration and migration operations retain their separate exclusive admission.

Prepare the pinned runtime, then the source index:

```bash
uv run --locked --no-sync rikishi bootstrap
uv run --locked --no-sync rikishi index
uv run --locked --no-sync rikishi verify-source
uv run --locked --no-sync rikishi doctor
```

Bootstrap downloads and builds tools. It verifies the pinned upstream revisions,
refuses conflicting local work, and applies the declared checksum-guarded Sigma
compatibility patch. Inspect [runtime setup](runtime.md) before running it,
including Java, prover, profile and stopped-server requirements. Budget disk and
memory for independent profile and evidence copies; a large source profile is
copied per invocation.

Serve the local inspection workbench only after its inputs are ready:

```bash
uv run --locked --no-sync rikishi dashboard --port 8765
```

Open `http://127.0.0.1:8765/#corpus`. The Hypertext Transfer Protocol (HTTP) and Model Context Protocol (MCP) inspection interfaces do not
launch solvers. `rikishi mcp` uses standard input/output and must be launched by
the intended client. Neither interface should be exposed as an authenticated
multi-user network service without a separate design and qualification.

## Formalization and manuscript prerequisites

Lean compilation additionally needs the pinned `fep_formal` source, compiler and
dependency artifacts. Use the explicit `--repo`, `--compiler`, `--packages` and
fresh `--output` options documented in [finite methods](fep.md). Do not modify
the canonical formalization checkout or silently replace missing proof inputs.

The complete manuscript needs the pinned template renderer, Pandoc,
pandoc-crossref, BibTeX, XeLaTeX, Poppler and the separately generated research,
inference, shared-witness and cache packets. Native tests also require the exact
selected Chromium executable. Follow the [manuscript recipe](manuscript.md),
which distinguishes acquisition, execution, replay and rendering. A portable
calculation or catalog listing cannot substitute for those prerequisites.

Use [reviewing the manuscript](review.md) to evaluate an artifact and
[release preparation](release.md) to prepare distributable files. Consult the
[current-state guide](current-state.md) and the version's actual receipts before
claiming any platform, native, visual or publication result.
