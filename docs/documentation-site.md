# Versioned documentation site

The Markdown sources are the source of truth. `tools/build_documentation.py`
builds an offline static site with version banners, original light layout,
sidebar, heading anchors, tables, local assets and a title search index.
`markdown-it-py` is a generic **development-only** parser (MIT); neither its
code nor its dependencies are vendored in the package. Runtime has no change.

```bash
python -m pip install "azimlib[docs]"
python tools/build_documentation.py --output .ci-results/site --ref dev/0.3.0
python tools/check_documentation_site.py --site .ci-results/site
```

The output must be a new directory; it is written atomically. Existing output
is never recursively removed. Sources/assets are allowlisted from docs and root
public policy files. Links to Python source become GitHub links for the selected
ref. Markdown links become HTML links; local binary/PDF/SVG assets preserve exact
bytes and legal notices. Raw HTML is disabled in Markdown rendering. No tracking,
external font, remote script or parser implementation is shipped with the site.

`docs.yml` builds/audits an artifact for development. Deployment is a separate future manual step and requires the GitHub Pages
environment/source to be configured. This preview workflow does not deploy. Development docs belong under `dev/`; stable docs belong under their
version (`0.2.0/`, later `0.3.0/`), never silently overwriting another version.
A hosted URL is not claimed until an actual successful deployment and HTTP check.
PyPI publication remains a separate manual action after all release gates.
