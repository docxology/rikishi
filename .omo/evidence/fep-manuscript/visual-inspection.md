# Manuscript visual inspection

Invocation: `pdftoppm -scale-to 1100 -png output/manuscript/pdf/rikishi.pdf .omo/evidence/fep-manuscript/page`

Inspected `page-1.png`, `page-2.png`, `page-3.png`, and `page-4.png` with the image
viewer. All four pages are readable; no clipping or overlapping content observed.
Page 2 contains both mathematical expressions. Page 3 contains the generated plot,
with visible axes, legend, posterior marker, and caption. The figure floats to the
next page in ordinary LaTeX layout. Page 4 retains the limitations and source links.

PDF SHA-256 inspected: `c3600bbbf8ef81e97ca475f28a9d8e6042a5c702aa2f8cb21d24e4eac20e1a4a`.
This inspection covers PDF appearance; DOCX and HTML receive structural/content
checks through `scripts/verification-manuscript.py`, not a claim of native Word UI QA.
