# Validação — Azimlib 0.5.0 Fase B

Branch `dev/0.5.0`, base exigida
`b991407f6efdb0c389f68e09025774889536fbab`. Desenvolvimento `0.5.0.dev0`,
sem release, tag ou publicação de documentação. As marcas da checklist
representam o recorte científico documentado, não suporte planetário universal.

## Evidência rastreável

| IDs 0.5.0 concluídos nesta fase | Implementação/evidência |
|---|---|
| 3.01–3.02 | SurfaceProjection, contexto físico, esfera/oblato, inversas, horizonte, emenda e polos; MetricProjections |
| 3.03 | BodySurface: distâncias, azimutes, rotas, comprimento e áreas em domínios explícitos; SurfaceGeodesy/fixtures independentes |
| 3.04 | PlanetaryRaster.profile: distância geodésica/projetada, alturas/unidades, fonte, resolução, máscaras e amostragem |
| 3.05 | Investigação de Jacobi/ODE, métrica de área, geodésia poliédrica e planificação; limites e recusas, **nenhum solver não oblato entregue** |
| 3.06 | Corpus PROJ/GeographicLib/CSPICE, domínio congelado antes da avaliação, casos adversariais e analíticos |
| 4.01 | PlanetaryRaster imutável/contextual, affine de cantos, unidades, máscaras/NoData, proveniência e RasterBudget |
| 4.03 | Hillshade, SurfaceFrame, SurfaceArtist/Mesh/texture existentes, alturas científicas e exagero local separados |
| 6.01–6.03 | GeometricLight/GeometricTerrainLight, direção/posição fixas explícitas, normais/terminadores reais e BVH de sombras |
| 6.06 | Normais CSPICE, incidência analítica, terminador finito/direcional e limites previamente definidos |

São **12 novos +17 anteriores =29/122 concluídos; 93 abertos**.
3.05 conclui a investigação solicitada, não a capacidade científica investigada.
2.04 e 9.02 continuam abertos, com integração parcial real documentada.
4.02/4.04–4.06, 6.04–6.05 e os itens transversais não são promovidos por analogia.
Todos os 122 IDs e descrições originais permanecem; quatro gates adiados da
0.4.0 continuam intocados. Próxima fase é C, mediante decisão separada.

## Precisão observada, não certificação universal

O relatório estruturado associado identifica SHA-256 do corpus, versões de QA,
hashes do código e resultados. Há 192 pares XY/inversa dentro de domínio,
15 verificações de recusa de domínio, 30 distâncias, 25 pares de azimutes
únicos, 19 áreas e 25 normais: **498 verificações aprovadas**.

| Grandeza | Maior erro observado | Critério prévio |
|---|---|---|
| XY, todos os métodos do corpus | 0,004037 m (TM regional) | 1e-5 m esfera; 0,05 m oblato; 0,5 m TM |
| Inversa | 1,592e-12 grau | 1e-8 grau |
| Distância geodésica | 0,000139 m | 0,05 m; difíceis 0,1 m |
| Azimutes únicos | 7,009e-8 grau | 1e-7 grau |
| Normal elipsoidal | 1,666e-16 | 1e-10 |
| Área | 282,737 m², em polígono muito grande | max(10 m², 1e-7 relativo) |

O erro de área deve ser lido com tamanho/erro relativo por caso, não comparado
a um budget absoluto de 10 m² para todo o planeta. Nenhuma tolerância foi
relaxada após avaliação. Fixtures são valores factuais gerados por oracles
externos; os testes congelados não dependem dessas bibliotecas.

As formas são ideais e estáticas; não há precisão de missão, areoide/geóide,
rotação IAU temporal, ciência triaxial/irregular ou atmosfera certificada.
O guia [surfaces-0.5.md](surfaces-0.5.md) contém a matriz efetiva e recusas.

## Formatos, compatibilidade e galeria

`examples/planetary/surfaces_050.py` gera 17 cenas reais Azimlib, cada uma em
PNG/SVG/PDF, com `index.html` e `gallery.json`: Terra globo/região, Marte global/
ortográfico/regional TM/polar/hillshade/3D/textura/incidência, Lua global/perfil/
hillshade, Vênus, Mercúrio e comparação de contextos. Dados não terrestres são
sintéticos determinísticos BSD-3-Clause, claramente identificados; não são
imagens orbitais observadas. Células grosseiras e malha global aberta são
limitações explícitas. SVG/PDF 3D incorporam raster do backend existente.

As cenas Brasil/estados/rota/escala e globo ortográfico foram comparadas à fonte
publicada 0.4.0, `50b467e252afe314645c031629ed1729007b267c`, com mesmo ambiente/
dimensões/DPI. PNG/SVG dessas duas cenas são a regressão byte a byte; não se
promete igualdade de pixels em todas as plataformas. Os exemplos históricos
da Fase A passam a pedir `projection='angular'` explicitamente, preservando
sua semântica não métrica; relatórios antigos não são reescritos.

## Testes, recursos e plataformas

Os resultados completos desta rodada, skips, benchmarks, auditorias e hashes
dos pacotes de desenvolvimento ficam no registro estruturado de validação.
Testes de sockets locais exigem loopback disponível; falhas de permissão do
sandbox são mantidas no registro privado, nunca ocultadas como aprovação.
Não foram suprimidos testes ou alteradas tolerâncias históricas.

Medições da galeria são diagnósticas: primeira cena e três cenas quentes,
dimensões/DPI fixados por exemplo, CPU, cache limitado. `--profile-memory`
mede alocações Python/tracemalloc separadamente e interfere nos tempos.
Isso não mede toda a RSS nem garante FPS/p95; não herda o gate GPU adiado.

O workflow não publicador `planetary-surfaces-0.5.yml` gera contratos e renders
em runners Windows/Linux/macOS, apenas em dev/0.5.0. Seu resultado deve ser
consultado pelo SHA exato: execução local Windows não certifica outros sistemas.
Não inclui aceite humano final da futura release, contratos GPU planetários
ou suporte HTML/browser ainda recusado. A fase C não é iniciada automaticamente.
