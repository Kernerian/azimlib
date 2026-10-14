# Observed validation — 0.4 development

These are historical results of snapshot
`d6ef84cfeb56c7fa6ca1e830a94718ed66195384`, not validation of a future release
candidate or universal accuracy/performance promises. [Structured values and
source report hashes](observed-validation-0.4.json).

## GPU

Windows, Ryzen 5 5600X / RTX 2060, NVIDIA 617.42, OpenGL 3.3, Python 3.14.4.
Fixed 700x500 scene, 100 DPI; five processes, 24 warm-up and 120 measured
frames per phase/process (600 measured per phase), all runs retained.

| Exact frame | Median ms | p95 ms | Variance ms² | 33 ms p95 |
|---|---:|---:|---:|---|
| Warm | 19.246 | 26.798 | 8.014 | Passed in this workload |
| Pan | 34.146 | 44.268 | 21.861 | Failed |
| Resume | 35.800 | 45.931 | 23.134 | Failed |
| Zoom | 85.108 | 103.559 | 80.968 | Failed |

Provisional p95 pan/resume/zoom: Tk 17.360/15.488/21.260 ms;
Qt 9.357/9.067/23.133 ms. Continuous provisional pan/resume cadence:
Tk 70.44/67.21 FPS, Qt 115.09/117.91 FPS. These are previews, not exact frames.
Native complete-response zoom p95: Tk 214.288 ms, Qt 143.758 ms, both above
100 ms. Eight isolated synthetic native gestures per phase; physical
input-to-photon latency was not measured. First native cold/warm paint:
Tk 1746.520/40.069 ms; Qt 1679.349/37.535 ms.

97/97 final GPU RGBA frames match the previous GPU oracle byte for byte.
CPU/GPU RGB MAE is separately 1.115347619/255 (Tk) and 1.221858168/255 (Qt),
alpha MAE zero; CPU/GPU pixels and cross-platform pixels are not identical.
Sampled aggregate process RSS: Tk 323956736, Qt 364244992 bytes, not driver VRAM.

[Development CI](https://github.com/Kernerian/azimlib/actions/runs/38493855546)
passed 6/6 jobs: Windows x64, Linux x64/ARM64, macOS x64/ARM64 and Mesa.
ARM64 native fallback/contracts and software Mesa are NOT physical GPU
performance evidence. GPU physical ARM64 remains an unmet part of deferred 9.08.

## Eclipses

Frozen corpus: 82 events (52 solar, 30 lunar). Preserved independent comparisons:
5118/5118 centers within 2 km, maximum observed 1.811 km; 489 solar contacts
maximum 8.65248 s; 150 lunar contacts maximum 30.5347 s; 195 magnitudes maximum
0.00063769; 137 solar obscurations maximum 0.000831888.

These maxima describe tested cases and quantities, not bounds between samples,
all epochs or unrepresented physical components. 10162 earlier boundary checks
contain 9941 numerical matches to the represented graph and **221 unresolved**
checks; graph distance does not certify the complete physical boundary. Round 8
did not replay that matrix because temporal physical completeness was unproved.

The 2023 center-oracle correction and historical references remain preserved.
1986 solar-radius convention/classification, invalid polar observer references,
independent numerical lunar obscuration and physical temporal envelope proof
remain open. Synthetic temporal/topological tests do not certify real events.
`accuracy_validated=False`, `certified_accuracy_interval=None`.
1972-2100 is an experimental computational domain, not certified precision;
explicit TT/UT1 and refusal outside supported inputs remain required.

Eclipse Predictions by Fred Espenak, NASA's GSFC. Source hashes and conventions
are preserved in the [deferred-gate register](deferred-gates-0.4.json).

## PBF

Own reader validated against regional real data, XML fixtures, corruption,
disk references, streaming and resource limits. Full-planet processing was
not executed; [2.08](planet-trial.md) remains deferred until suitable infrastructure.
No regional extract is a substitute for that evidence.
