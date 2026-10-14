# Azimlib 0.4.0 — unreleased, re-scoped development draft

This is not final acceptance or publication approval. Candidate metadata is 0.4.0; the published package remains 0.3.0. No accepted final 0.4 release, tag or uploaded PyPI files exist.

## Functional development additions

- Own bounded PBF stream/index and regional real-data extraction; CRS/datum
  grids, planar/spherical topology, local geocoding and own road routing.
- Optional international shaping/fonts and explicit external TeX toolchains.
- Optional experimental own GPU rendering and bounded 3D volume visualization.
- Terrestrial bounded Sun/Moon Artists, Earth–Moon views, local physical lighting
  and experimental finite-body eclipse visualization with explicit conventions.
- Familiar root/pyplot imports, CPU defaults, editable/optional map components
  and separated static export/interactive viewers preserved.

## Scope and limits

[Original inventory](release-progress-0.4.md): 112 stable IDs, **107 completed,
four deferred, one pending delivery/revalidation**. Historical 14.01/14.06
results remain historical. Fresh revalidation and exact hosted CI/distribution are recorded separately in
[the operational evidence](stage14-execution-0.4.json). Native human acceptance (14.05) is recorded, including TeX. Final acceptance/publication (14.08) remains pending; a documentation-only successor requires new CI and packages.
[Decision, original criteria and hashes](deferred-gates-0.4.md).

2.08 planet trial, 9.08 full GPU performance and 13.06/13.07 scientific eclipse
certification are formally deferred, not completed. [Observed validation](observed-validation-0.4.md)
reports measured previews, exact frames, parity, platforms and corpus results
alongside unresolved checks. There is no guaranteed 33 ms p95/100 ms response,
complete physical eclipse envelope/certified global forecast, or proven planet scale.
1972-2100 is an experimental computational domain, not a certified accuracy interval.

0.4.1 is for compatible fixes/refinements and planet testing only with suitable
infrastructure; scientific closure is not promised. 0.5 remains Planetary
Cartography / Beyond Earth, 0.6 remains Orbits. Deep foundations may support
these versions without making global eclipse certification mandatory.

## Still required before release

14.01/14.02/14.03/14.06 were revalidated; 14.04/14.07 have exact-SHA CI and
distribution evidence on the previous candidate. 14.05 is explicitly approved;
repeat CI/build/audits on the successor. 14.08 final acceptance/publication remains open. [Current record](stage14-0.4.md).
Rescope tests and prior development CI are not those final gates.

The strict publication checker now enforces the scoped release contract,
with only the four named deferrals,
not an unchecked-ID bypass. Runtime regressions, corruption, resource violations,
licensing/privacy failures and unresolved delivery items continue to block release.
Only separate explicit authorization permits tags, GitHub Release, public docs
or PyPI; retain exact commit/artifact identity and audit final distribution bytes.

## Unpublished preparation and publication gate

Stage-14 tooling distinguishes `--purpose prepare` from the default publication
gate. Preparation permits only 14.04/14.05/14.07/14.08 to remain open; it is not
publication approval. Publication requires all 108 active IDs complete, exactly
the four named deferments still unchecked, and no other unchecked ID. Human
14.05 and explicit final 14.08 acceptance cannot be inferred from CI.
