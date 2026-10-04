# Referência anterior do renderer próprio

Snapshots de `pillow.py` e `coverage.py` extraídos do wheel Azimlib 0.1.0
validado antes das otimizações de 2026-09-30. São código da própria Azimlib,
sob a licença BSD-3-Clause do projeto, sem Matplotlib ou outro backend geoespacial.
Não são importados pela biblioteca nem instalados no wheel.

`tools/compare_raster_versions.py` usa esses arquivos serialmente sobre a mesma
Scene, alternando antes/depois. Ele registra SHA-256 dos fontes e dos PNGs.
É uma referência de desenvolvimento para essa alteração específica, não uma
garantia de compatibilidade com futuras primitivas/cenas da biblioteca.
