# Versioned documentation site

Markdown sources are the source of truth. `tools/build_documentation.py`
builds an offline static site with version banners, an original light layout,
sidebar, anchors, tables, local assets and title search. `markdown-it-py` is
generic development-only MIT tooling; it is not vendored or a runtime dependency.

```bash
python -m pip install "azimlib[docs]"
python tools/build_documentation.py --output .ci-results/site --ref main
python tools/check_documentation_site.py --site .ci-results/site
```

For a reproducible deployment, pass the exact documentation commit to `--ref`.
It may be newer than the immutable release tag: documentation corrections do
not rebuild, replace or reupload published distributions. The site manifest
records the selected ref, version and source hashes.

Output must be a new directory and is written atomically. Sources/assets are
allowlisted from docs and root policies. Markdown links become HTML links;
Python source links use the selected ref. Binary/PDF/SVG assets retain exact
bytes and legal notices. Raw HTML is disabled in Markdown. No tracking, external
font, remote script or parser implementation is shipped with the site.

## Publication and verification

`docs.yml` builds an audited preview artifact; it does not deploy. Deployment
uses a separate `gh-pages` branch. Versioned documentation belongs under
`0.3.0/`; `stable/` selects the stable documentation and `dev/` currently mirrors
0.3.0. Historical source evidence remains separately identified.

- [Stable documentation](https://kernerian.github.io/azimlib/stable/)
- [Version 0.3.0](https://kernerian.github.io/azimlib/0.3.0/)
- [Development alias](https://kernerian.github.io/azimlib/dev/)
- [Package publication evidence](release-publication-0.3.0.md)

Before deployment, check source hashes, asset bytes, local links, license
notices and privacy, including decoded PDFs and image metadata. Check the
staged Git payload against that reviewed site. After deployment, require a
successful Pages run and compare public HTTPS files against reviewed bytes.
PyPI publication is separate; updating documentation must not modify packages.

## Git attributes in the Pages branch

Preserve reviewed payload bytes with `* -text`. CRLF text must be checked with
`whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol`, keeping the
default whitespace checks while recognizing CR as part of a line ending.
Declare PDF, PNG, GIF, JPEG, icon and font exports binary. Do not trim PDF
whitespace: xref records, offsets and embedded notices are format-defined.
Validate binary exports through hashes, source byte equality and format checks,
not a text whitespace checker. Trailing text spaces, extra blank EOF lines
and spaces before tabs must continue to fail the Git gate.
