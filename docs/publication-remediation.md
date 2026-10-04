# Public-distribution remediation — 0.2.0

This is a technical status record, not a legal opinion. It covers the local
prepared repository and named rebuilt artifacts. No PyPI upload, GitHub push,
release creation or visibility change was performed.

## Findings and disposition

| Finding from the IP/privacy audit | Status | Concrete evidence / disposition |
|---|---|---|
| ColorBrewer Blues lacked its complete specific terms and required acknowledgment | **RESOLVIDO** | `THIRD_PARTY_LICENSES.md`, `licenses/LicenseRef-ColorBrewer.txt`, referenced `licenses/Apache-2.0.txt`; complete texts and hashes in `licenses/upstream.json`; package metadata includes LicenseRef-ColorBrewer |
| Category10/TAB10 incorporation route was not established | **RESOLVIDO** | `src/azimlib/cycles.py` has new AZIM10; TAB10 aliases AZIM10; `config.py` and historical source baselines use it; old reference observations are explicit comparison inputs, not defaults |
| Additional dark style cycle coincided with the reference preset | **RESOLVIDO** | `style.py` lightens AZIM10 using a documented own rule; both retired sequence fingerprints are checked by `tools/audit_licenses.py` |
| Third-party materials were insufficiently separated from original-code ownership | **RESOLVIDO** | Inventory, per-material origins/copyrights/terms, complete separate license texts and `src/azimlib/data/materials.json`; no claim of exclusive rights in external materials |
| Natural Earth provenance and publisher terms must remain | **RESOLVIDO** | Six compressed geographic layers are byte-identical; `data/manifest.json` retains source commit ca96624a56bd078437bca8184e78163e5039ad19, hashes and feature counts; `licenses/Natural-Earth.txt` records the publisher's public-domain statement |
| DejaVu fonts and derived metrics must not be relabeled original/exclusive | **RESOLVIDO** | Four unchanged 2.35 TTF binaries verified against `docs/fonts-upstream.json`; complete `fonts/LICENSE_DEJAVU` unchanged; font README and inventory explicitly separate metrics and font rights |
| CC0 color tables needed preserved provenance | **RESOLVIDO** | `NOTICE_COLORMAPS` unchanged; complete `licenses/CC0-1.0.txt`; four 256-sample tables retain their upstream authors and origin in materials inventory |
| Copyright label was inconsistent / legal entity not established | **RESOLVIDO** for the public notice | Original-code `LICENSE` and metadata use Kernerian consistently. It is a public identifier, not an invented company or proof of civil identity / legal title |
| Original-code MIT text and package metadata needed replacement | **RESOLVIDO** | BSD-3-Clause applies to original implementation/docs/icons; pyproject uses the composite SPDX expression; legitimate third-party MIT terms and historical measured MIT metadata remain distinctly identified |
| Personal paths, conversation quotations, requests and approvals in documents/reports/comments | **RESOLVIDO** within scanned scope | Portable paths, neutral technical records and `publication_privacy.py`; current tracked files and all local refs/reflogs pass the publication scan |
| Removed private content remained recoverable in Git history | **RESOLVIDO** locally | All original five commits were rewritten; main and fix/ci-portability preserved; old objects/reflogs pruned; `git fsck --full --no-reflogs` passes; technical files retained |
| Previously reused reference icons, removed before the available Git history | **NÃO APLICÁVEL** to current deliverables | No such assets in available sanitized history/package; 21 original icon resources, geometry SHA-256 45d5a0016aaa7617a35b737fdfbe43953699acf45099ee795bfd0abb668b1823; zero byte matches against 32 reference icon files. Pre-Git events cannot be reconstructed exhaustively |
| Old 0.2.0 archives contained stale MIT metadata / unsanitized source | **RESOLVIDO** for deliverables | Fresh wheel/sdist and source ZIP; old archives quarantined outside this repository in private recovery storage; RECORD, License-File payloads and source equality audited |
| Privacy/license checks were not recurring distribution gates | **RESOLVIDO** | New targeted tests, `audit_licenses.py`, archive/history scanner and explicit source/archive CI gates; this does not imply the modified workflow ran remotely |
| GitHub still has original commits, PR refs, cached views and Actions data | **AINDA PENDENTE** | Local rewrite deliberately does not push. Before public visibility, coordinate server-side history replacement and inspect/remove retained PR/Actions/cache objects as applicable; another clone/fetch can restore the old history |
| Corrected bytes lack a new three-system CI run | **AINDA PENDENTE** | Previous 24-job records are explicitly historical; updated local Windows results are separate. A new remote run requires sending the corrected repository later |
| IBGE benchmark dataset-specific redistribution terms were unconfirmed | **NÃO APLICÁVEL** to current deliverables | Original external inputs remain excluded and are explicitly prohibited by distribution checks; confirm their license before any future bundling |
| Optional dependency binaries and future dependency resolution | **NÃO APLICÁVEL** to this wheel's embedded materials | Wheel embeds no third-party Python/native dependency. Separate installs retain their own licenses; a future combined installer requires review of its exact Pillow/NumPy/Numba/LLVM/codecs payloads and exceptions |
| Exclusive authorship, AI-related title, trademark/patent clearance | **AINDA PENDENTE** as legal assurance | No problematic source derivation was found in the technical audit, but source comparisons/Git labels do not prove exclusive title or legal clearance. Professional legal review is required for that assurance |

## New local verification

- Installed wheel, Windows / Python 3.14: **682 tests, 16,795 subtests**, passed;
  two compiler-only tests skipped in the GUI environment without Numba.
- Optional compiler environment: **11 tests, 5,470 subtests**, passed without
  skips. No forbidden runtime imports in either run.
- All **13 real Tk integration scripts** passed, including layout, toolbar,
  pan/zoom, lifecycle and raster caching. This is synthetic integration,
  not another human appearance or latency acceptance.
- Python 3.11: seven new publication tests and 21 series/style contracts passed.
- Fresh dependency-free installation passed SVG/HTML/data/fonts/artist smoke.
- **19 own-renderer gallery cases** exported at 100 DPI; three starter SVGs
  executed. Documentation local targets passed with the audited local gallery.
- Complete separate license texts, six geographic layers, four fonts, original
  icon hashes, static runtime independence and archive metadata/RECORD checked.
- Privacy checks scan tracked files, all local refs/reflogs, reachable objects
  and delivery archives; they are pattern-based, not exhaustive secret detection.

Raw machine reports and archive hashes are under `.ci-results/publication-*`,
outside wheel/sdist/ZIP. The explicit `publication-source-map.json` maps changes
to old snapshots without relabeling old runtime hashes as new execution results.
All original tracked file paths remain present; only identified legal/privacy/
palette consequences and validators/docs were changed.

## Legal and publication boundaries

BSD-3-Clause governs the original code; it does not replace ColorBrewer,
DejaVu, CC0 or Natural Earth terms. Existing copies previously received under
MIT cannot have those permissions revoked by rewriting a local repository.
The change applies to the prepared distribution under the holder's authority;
it does not establish ownership over third-party contributions by fiat.

Recovery bundles/old archives intentionally remain private outside the release
repository and must not be included in any public upload. Technical absence of
known problems is not a “100% free” certification or substitute for professional
legal advice. Do not make the GitHub repository public before the separate
server-history check; no server erasure is claimed here.
