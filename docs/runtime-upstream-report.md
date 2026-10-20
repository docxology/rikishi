# Local upstream report: compound class type guards flatten into invalid TPTP

This is a local report for **ontologyportal/sigmakee**, not a published issue.
The runtime was tested at Sigma commit
`d3cc7b43b38b0b45692291a1b33fe2b1a3de0095`, SUMO commit
`efcd059f8feebfe3488a09f575f88d4d009b1e5c`, Java 21.0.12.1, and the pinned E
source revision in `config/sumo.lock.json`.

`FormulaPreprocessor.buildTypeGuardExpr` constructs `Expr.Atom(type)` for both
instance and subclass guards. SUMO's mid-level ontology contains a compound
class type `(ExtensionFn Oval)` for the tangent relation. That type becomes an
atom containing parentheses and a space. The FOF translator then emits the
invalid symbol `s__(ExtensionFn Oval)` instead of a functional term.

The actual generated file failed E parsing at line 840, column 188:

```text
Closing bracket (')') expected, but Identifier not terminating in a number read
```

The invalid generated file is retained locally at
`.omo/evidence/runtime/SUMO-unpatched.tptp`; invoking the installed E executable
against that file reproduces the syntax failure without rebuilding Sigma.

The compatibility patch in `config/patches/sigma-compound-type-guards.patch`
uses Sigma's existing `SuokifVisitor.parseAny` for compound types and retains
`Expr.Atom` for atomic types. It makes the same correction in the subclass-guard
branch. The Java regression at `scripts/runtime/RuntimeTypeGuardRegression.java`
tests both compound branches and an atomic control. The original JAR fails the
regression, while the rebuilt patched JAR passes. Hashes for the patch and the
source before and after application are locked. No SUMO assertions change.

An additional observed integration issue is that `KB.main` can submit an E
problem before asynchronous FOF generation finishes, and prints only ATP stdout,
hiding a useful parse error on stderr. Rikishi's adapter generates FOF
synchronously and writes a separate structured report from `ATPResult`, including
actual ATP exit status, output count, and stderr. A missing ATP result is an
explicit failure even if Java exits zero. This avoids interpreting a query echo
containing `SZS status Theorem` as an actual prover response.

After the type-guard correction, E reports `Theorem` for
`(subclass Human Animal)` and `ContradictoryAxioms` for the unrelated
`(subclass Human Artifact)` control under the four-constituent core profile.
That latter result is retained as a separate unresolved diagnosis; the type-guard
patch does not establish that the complete translated core theory is consistent.

Evidence index: `.omo/evidence/runtime/README.md`.
