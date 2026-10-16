# Operational legal-payload validation for 0.4.0

The release source remains `50b467e252afe314645c031629ed1729007b267c`.
The annotated v0.4.0 tag, existing distributions, metadata and product
documentation are immutable. This operational tooling is versioned separately
from those release inputs on the publication-authorization branch.

`tools/check_verbatim_legal040.py` requires `git diff --cached --check` for all
staged publication paths except six explicitly enumerated AMSFonts/LPPL copies
under 0.4.0, stable and dev. There are no directory or extension exemptions.
Each exception requires presence, ordinary-file mode, exact worktree/index
agreement, the frozen SHA-256, and byte equality with the original legal Git
object from the approved source commit. Future byte changes require a new
audit and explicit registry review. Do not trim, normalize or rewrite licenses.

Run the gate with the Pages checkout and the repository holding the immutable
release objects. No paths from a particular workstation are required:

```sh
python tools/check_verbatim_legal040.py --repository PAGES_CHECKOUT --source-repository RELEASE_REPOSITORY --output legal-preflight.json
python -m unittest discover -s tests -p test_verbatim_legal040.py -v
```

For tests from a standalone operational checkout, set
`AZIMLIB_AUDITED_SOURCE_REPOSITORY` to the repository containing the approved
release objects. Test fixtures use the actual audited licenses; their hashes
and the exception registry are never patched to make a test pass.

The tooling does not authorize another release SHA or other package bytes.
Publication must still validate the exact authorization, original 70-job CI,
artifact provenance, package hashes, licenses, privacy, distribution contents,
installation and public documentation. Authorized does not mean completed.
