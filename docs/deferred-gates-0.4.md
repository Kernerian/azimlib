# 0.4.0 development rescope and deferred gates

Decision date: 2026-10-14. This is a scope decision, not scientific acceptance,
publication approval or a claim that deferred criteria passed.
[Structured register](deferred-gates-0.4.json), [current checklist](release-progress-0.4.md),
[historical checklist](release-progress-0.4-before-rescope.md).

Original inventory: 112 IDs. Current: **107 completed, 4 deferred, 1 pending
delivery/revalidation**. Active 0.4 scope: 107/108. Historical 102 completed
included 14.01/14.06; both have separate revalidation; exact CI/distribution passed on the recorded SHA.
Only final acceptance/publication remains pending; new commits require revalidation.
Stage 14 preparation is now tracked separately in [the current record](stage14-0.4.md). 14.05 has explicit human acceptance; repeat exact-SHA CI/distribution after recording it. 14.08 remains pending.

| Original ID | State | Unmet criterion / destination |
|---|---|---|
| 2.08 | Deferred, not completed | Only the real full-planet trial remains; attempt in 0.4.1 if infrastructure exists |
| 9.08 | Deferred, not completed | Frozen 33 ms exact p95 / 100 ms complete response and physical ARM64 GPU evidence; compatible refinements in 0.4.1, deep foundations for 0.5 |
| 13.06 | Deferred, not completed | Global supported physical precision and complete temporal/visible envelope; separate research track |
| 13.07 | Deferred, not completed | Independent valid references and all required comparisons within fixed tolerances; no promised closure version |

The register stores every original criterion verbatim and its SHA-256. Original
contracts and private evidence manifests retain their hashes. Copies of the
[frozen GPU protocol](deferred-gpu-protocol-0.4.json) and
[scientific budget](deferred-eclipse-budget-0.4.json) are byte-identical to their
archived originals. Raw reports/references remain in the maintainer archive;
do not distribute private paths, raw logs, conversations or large external datasets.

## Unchanged acceptance and historical evidence

- GPU: exact frame p95 <=33 ms, complete response <=100 ms, memory/parity,
  frozen repetitions/workload and physical ARM64 GPU subgate remain.
- Science: centers 2 km, boundaries 3 km, solar contacts 30 s, lunar contacts
  60 s, magnitude/obscuration 0.001; no relaxed tolerances or removed failures.
- Planet: complete real dump, date/SHA-256, EOF, counts, memory/disk/time and
  zero missing/corrupt references under the [existing procedure](planet-trial.md).
- [Observed results](observed-validation-0.4.md) keep successes and unresolved
  checks distinct. No failed/indeterminate check was converted to a pass.
- Later evidence must name the version/commit that fulfills a gate. It must not
  retroactively certify the released 0.4 implementation or rewrite old reports.

Only these four explicitly identified requirements are deferred out of the
0.4 delivery scope. Functional regressions, corrupt outputs, resource violations,
licensing and privacy failures still block delivery. The scoped release checker remains fail-closed and must not silently ignore
arbitrary unchecked IDs. Preparation and publication are separate purposes.

## Future sequence

0.4.1 preserves supported public signatures/semantics and accepts compatible
fixes/refinements. Planet trial is conditional on infrastructure; scientific
gates have no promised completion in that patch release.

0.5.0 remains **Planetary Cartography / Beyond Earth**: public body models,
body-specific coordinates/geodesy/projections, planetary DEMs/images, relief,
illumination and existing map Artists. Deep renderer/science changes can serve
these foundations. Global eclipse certification is not a mandatory 0.5 gate;
scientific APIs remain experimental until evidence supports promotion.
0.6.0 remains **Orbits**, with the existing planned sequence intact.

## Stage 14 after review

14.01 and 14.06 require renewed integrated regressions and license/provenance/privacy
audit on the final candidate; their older evidence is historical only. 14.02
must reconcile public docs/claims; 14.03 consolidates measured budgets including
failures; 14.04 requires complete exact-candidate CI; 14.05 requires the applicable
native human review; 14.07 covers metadata/build/install/hashes and explicitly
scoped fail-closed release tooling; 14.08 requires final approval of the exact
commit/artifacts before any external publication. None is completed by this document.

## Unpublished preparation and publication gate

Stage-14 tooling distinguishes source preparation, authorized publication preflight,
and verified post-publication completion. Preflight requires 107 completed IDs,
exactly the four named deferments, only 14.08 unchecked, and separately versioned
human authorization bound to the exact SHA, audited hashes and successful CI.
Authorization is not completion. Only validated post-publication observations
permit the operational 108 active completed total. [State contract](release-publication-state-0.4.md).
