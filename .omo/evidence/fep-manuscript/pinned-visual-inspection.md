# Pinned renderer verification

This run supersedes the earlier live-checkout renderer receipts. The original
template worktree had unrelated active-owner modifications. It was preserved;
the renderer now imports only the verified archive snapshot at
`efce6d6f5b3c4e8e2bbf92d8250855a0a9389ae8`.

`pinned-final-receipt.txt` records actual checks: 256 imported source modules match
the archive manifest, seven artifact hashes match, PDF text and both embedded DOCX
figures pass, and both HTML figures exist. The snapshot positive control verifies
1,625 archived files. The negative control alters a separate temporary snapshot's
`pyproject.toml` and confirms that reuse is rejected with a mismatch error.

All five `pinned-page-N.png` images were generated with `pdftoppm -scale-to 900`
and inspected. Both charts, equations, corpus counts, proof scope, and limitations
are readable, with no clipping or overlap observed.

Inspected PDF SHA-256:
`b47451c87a80d7060ba75bf2202382d55cca5043d341757bb760ee7c23de5efc`.

The receipt records `template_worktree_clean: false` and
`template_worktree_used: false`; this distinction is intentional. Archive hash:
`4b3e086f104817f01e4d64c488ffe966d4f6651819c1775b7bba93a7f95d47fc`.
