# 0.4.0 candidate — measured evidence ledger

14.03 consolidates recorded measurements under the re-scoped release contract.
It does not rerun or close the four deferred gates. [Ledger and hashes](release-benchmarks-0.4.json).
The [latest observed GPU/science report](observed-validation-0.4.md) and
[older integrated workloads](integration-benchmarks-0.4.md) retain original
hardware, source identity, methods and failures. They are historical snapshots,
not final-candidate or universal performance guarantees.

| Area | Observed evidence | Target / limit | Unproved claim / deferred ID |
|---|---|---|---|
| GPU exact warm | p95 26.798 ms, recorded 700x500/100 DPI workload | 33 ms p95 | No universal guarantee; 9.08 |
| GPU exact pan/resume/zoom | p95 44.268 / 45.931 / 103.559 ms | 33 ms p95 | Target failed; 9.08 |
| Native complete zoom | Tk 214.288 / Qt 143.758 ms p95 | 100 ms response | Target failed; input-to-photon unmeasured; 9.08 |
| Final GPU frame reuse | 97/97 previous GPU-oracle frames byte-identical | Exact previous-path comparison | CPU/GPU identity and ARM64 physical speed not implied; 9.08 |
| PBF | Real regional Monaco, streaming, references and limits | Bounded reader/resource contracts | Strict recut rejects missing relations; regional skip is explicit. Full planet absent; 2.08 |
| Eclipses | Frozen centers/contacts/magnitude/obscuration observations | 2 km / 3 km / 30 s / 60 s / 0.001 | Physical temporal boundary completeness and remaining references unproved; 13.06/13.07 |
| Foundation/topology | Seven 1000-roundtrip batches; 20000 disjoint segments and analytic bounded cases | Original allocation/workload budgets | No dense arbitrary-overlay or global dataset throughput guarantee |

RTX 2060 / Ryzen 5 5600X, NVIDIA 617.42, OpenGL 3.3, Windows/Python 3.14.4;
five independent processes, 24 warm-ups + 120 measured frames per phase/process.
All runs retained. Sampled process RSS is not VRAM or a hard instantaneous quota.
Mesa and native ARM64 fallback establish contracts, not physical GPU performance.

Future refinements must retain before/after workload identity and report medians,
p95, variance, cold/warm cache conditions and full response separately. No
favorable-run selection or relaxed budget is authorized by this consolidation.
