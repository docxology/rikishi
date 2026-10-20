# Rikishi documentation

Start with the [project README](../README.md) for installation and executable
commands. Use these guides for the corresponding research or operator task.

| Task | Guide |
| --- | --- |
| Complete a first research workflow | [Tutorial](tutorial.md) |
| Develop a proposed ontology extension | [Modeling](modeling.md) |
| Preserve and reproduce evidence | [Reproducibility](reproducibility.md) |
| Install and diagnose actual SUMO tools | [Runtime](runtime.md) |
| Understand source, index, and reasoning boundaries | [Architecture](architecture.md) |
| Explore the visual interface | [Dashboard](dashboard.md) |
| Connect HTTP and MCP clients | [API](API.md) |
| Interpret the finite free-energy example | [FEP connections](fep.md) |
| Reproduce the PDF, DOCX, and HTML manuscript | [Manuscript](manuscript.md) |
| Evaluate acceptance evidence | [Verification](verification.md) |
| Prepare a justified SUMO issue or PR | [Upstream contributions](contributing-upstream.md) |

Machine-readable proposed correspondences live in
[`config/fep_mappings.json`](../config/fep_mappings.json). The example can also be
run directly through [`examples/fep_demo.py`](../examples/fep_demo.py). Agent
instructions are available under `.agents/skills/` with distribution copies in
`skills/`. Paths in those skills are relative to the repository root.

The inherited template exemplar lives in `template_reference/`; its historical
results and metadata are not Rikishi findings. The new manuscript source is
[`manuscript/rikishi.md`](../manuscript/rikishi.md), and its render receipt identifies
the actual output bytes and canonical template revision.
