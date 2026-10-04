# Contornos, linhas coincidentes e integração em mais mapas

Relatórios desse lote preservam seus hashes originais. As versões anteriores
de Tk/Pillow estão em `tools/baselines/interactive-tiles-before`; a auditoria
verifica esses snapshots, sem declarar tempos antigos como medições atuais.
Resultados atuais do viewer: [responsividade](pan-responsiveness.md).

Este lote fecha três subpassos no escopo local auditado:

1. Calcula diretamente a área dos recortes com cinco a nove vértices,
   traduzindo cada coordenada uma vez. Mantém todos os termos, inclusive os
   zeros, na mesma ordem de `sum`; não arredonda nem simplifica geometria.
2. Corrige linhas totalmente coincidentes: não desenha um traço sem segmento,
   independentemente da extremidade; marcadores explícitos continuam visíveis.
3. Amplia a comparação raster para mapas políticos, atlas, pontos, terreno,
   globo com vetores/rotas e municípios; integra globo/terreno com Tk e exports.

## Regra de linhas coincidentes

```python
import azimlib as azl

fig, ax = azl.subplots()
line, = ax.plot([-46, -46], [-23, -23], solid_capstyle="projecting")
# Sem segmento: nenhum traço. Um marcador pode ser acrescentado normalmente.
line.set_marker("D")
line.set_visible(False)
```

Antes, `round` podia gerar um ponto extra e `projecting` podia lançar
`AttributeError` durante PNG/Tk. O compositor e os renderizadores agora omitem
esses traços sem alterar o dado original ou seus marcadores. A comparação usa
igualdade exata de coordenadas, sem uma tolerância que descarte linhas curtas.
Partes válidas vizinhas de uma MultiLineString/Path permanecem renderizáveis.

[18 casos registrados diretamente](degenerate-strokes-reference.json) cobrem
três capstyles, um/dois/quatro pontos e presença/ausência de marcador. O contrato
adotado é o de visibilidade do **Matplotlib/Agg**. O SVG nativo ainda serializa
subpaths coincidentes; a Azimlib os omite para manter sua regra entre PNG, SVG e
viewers. Isso não promete equivalência entre todos os backends de Matplotlib,
nem igualdade dos pixels dos marcadores com Agg.

## Comparação de desempenho

```bash
python tools/compare_stroke_kernels.py --output kernels-100.json --dpi 100
python tools/compare_stroke_kernels.py --output kernels-200.json --cases state points terrain globe --dpi 200
python tools/compare_stroke_kernels.py --output municipal.json --cases municipal --geojson /caminho/base.geojson
```

Referência é o próprio `_area` anterior, preservado em
`tools/baselines/stroke-kernels-before/coverage.py`. O comparador troca apenas
essa função em uma cena fixa, alternando serialmente antes/depois. Composição,
PNG/SVG, hashes e I/O ficam fora do tempo de raster. Não usa cache de frames,
profiling simultâneo, downloads ou backend geoespacial externo.

[100 DPI](performance/stroke-kernels-100.json) contém sete cenários e
[200 DPI](performance/stroke-kernels-200.json) contém quatro: **11 cenários,
44 renders**, com RGBA/PNG idênticos em cada comparação. Valores de terreno,
vetores e pontos são sintéticos; fronteiras incluídas são generalizadas. A
base municipal fornecida pela API tem [proveniência e limites](municipal-raster.md)
e não integra o pacote.

O wheel instalado repetiu os mesmos onze cenários, uma chamada por modo/cenário:
[100 DPI](performance/stroke-kernels-wheel-100.json) e
[200 DPI](performance/stroke-kernels-wheel-200.json). Os 22 renders mantiveram
RGBA/PNG iguais antes/depois e os hashes RGBA/PNG/SVG coincidem com os do source.
Os tempos dessa rodada única não são agrupados com as medianas do source.

| Cenário/DPI | Antes (s) | Depois (s) |
|---|---:|---:|
| Brasil/100 | 3,859 | 3,740 |
| Atlas/100 | 5,580 | 5,354 |
| Municípios/100 | 13,027 | 12,677 |
| Terreno/100 | 0,895 | 0,912 |
| São Paulo/200 | 2,499 | 2,597 |
| Globo/200 | 4,711 | 4,620 |

São medianas de duas chamadas por modo, sujeitas à carga da máquina. Há variação
nos dois sentidos; não se declara aceleração geral ou significância estatística.
Estes valores não devem ser comparados diretamente com tempos de lotes anteriores,
obtidos em outras sequências/cargas. O tempo inicial de bases densas segue alto.

## Integração desktop

`tools/smoke_stroke_kernels_tk.py` verifica globo e terreno em Tk real oculto:
foco regional/Home, edições de marcador, visibilidade, 200 DPI, pixels do canvas
versus raster/PNG e exports PNG/SVG sem criar UI. Campos/rotas são sintéticos.
Os relatórios [source](stroke-kernels-tk-source.json) e
[wheel](stroke-kernels-tk-wheel.json) registram **12 verificações cada** e hashes
do runtime. A CI inclui este nono script desktop; execução remota nas três
plataformas permanece pendente. Janelas ocultas/entradas programáticas não medem
input físico, pintura visível ou a aparência real da toolbar do sistema.

O [progresso da 0.2.0](release-progress.md) continua por subpassos. Este lote
consolida recursos existentes; urbano, 3D e Qt permanecem depois desse corte.

Suíte cumulativa: **591 testes/14.022 subtests**, incluindo oito regressões/
5.887 subtests novos de aritmética/máscaras/pixels, linhas colapsadas e marcadores.
Os oito scripts desktop anteriores também passaram novamente no wheel instalado.

Os experimentos de tempo stroke-kernels-* preservam o renderer anterior ao
caminho transitório de navegação em `tools/baselines/interactive-raster-before/pillow.py`.
Seus hashes continuam conferidos contra esse snapshot; não são tempos do preview
novo. Smokes Tk e galerias atuais são repetidos com o runtime instalado atual.
