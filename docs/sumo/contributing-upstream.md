# Evidence-based upstream contributions

Rikishi can support issues and pull requests to
[`ontologyportal/sumo`](https://github.com/ontologyportal/sumo). This repository
does not submit automatically. Read the current upstream contribution instructions
and existing issues before preparing a report.

1. Record the exact ontology commit, runtime versions, operating system, and command.
2. Reduce the behavior to the smallest ontology fragment or query that reproduces it.
3. Retain stdout, stderr, exit status, and any proof output. Distinguish parsing,
   translation, theorem-proving, and user-interface failures.
4. Check whether the supposed defect is a consequence of documented semantics.
   Unknown or timed-out proof search does not establish inconsistency or falsehood.
5. Search existing upstream issues. Prepare a concrete report with expected and
   observed behavior, relevant axiom links, and an independently runnable reproducer.
6. For a fix, use a fork and isolated branch, add the narrow regression, run relevant
   upstream checks, and preserve original attribution and license notices.
7. Submit only when there is a justified finding and authorization to publish the
   included material. Remove local paths, credentials, and private research content.

Use `gh-axi issue` and `gh-axi pr` where available. Inspect each command's help for
its installed interface. A suitable issue title names the concrete failing operation.
The body should contain: revision, minimal reproduction, expected result, actual
result, and evidence. A suitable pull request (PR) describes the changed semantics and test evidence.

A proposed Free Energy Principle (FEP) alignment is normally a design discussion, not a bug report. Do not
present a mismatch between the Suggested Upper Merged Ontology (SUMO), Lean's totalized arithmetic, and this numerical
operator as an upstream defect until the intended contract is established.
