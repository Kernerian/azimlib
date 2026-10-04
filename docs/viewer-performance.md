# Raster direto e medições do viewer Tk

As medições abaixo preservam o código e os hashes da entrega original. O
[pan ao vivo](pan-interaction.md) de 2026-10-03 removeu o preview traduzido e
passou a redesenhar durante motion; os tempos históricos de pan não medem
essa nova implementação. Latência de apresentação/input permanece em 4.09.

O renderer próprio agora expõe `render_image(scene, scale=1)`, que devolve uma
imagem Pillow RGBA com o mesmo antialiasing, fontes e composição do PNG. Quem
recebe a imagem deve fechá-la. A importação do módulo não exige Pillow; essa
dependência opcional só é necessária ao renderizar.

```python
from azimlib.renderers import render_image

image = render_image(fig.to_scene())
try:
    print(image.size, image.mode)
finally:
    image.close()
```

`render_png` codifica essa imagem no arquivo/stream e a libera mesmo se a
gravação falhar. Streams do chamador permanecem abertos. `savefig()` continua
uma exportação estática PNG/SVG sem UI. `show()` usa o backend próprio: o Tk
encaminha RGBA a PhotoImage sem codificar, decodificar e converter um PNG
intermediário. Libera a imagem anterior após cada desenho e a atual no
fechamento. Não retém a Scene e a cópia raster iniciais: Home recompõe a vista
pelo histórico. Minimapa e demais componentes continuam opcionais.

Atualização de 2026-10-02: o Tk recompõe a cena e pode reusar pixels de uma
vista já visitada através de uma LRU limitada (quatro frames/16 MiB de RGBA
retidos). Home/histórico mantêm metadata e eventos atuais. Não há cópia inicial
dedicada nem cache na exportação estática. Veja [medição municipal e limites](larger-batch.md).
Os experimentos abaixo registram a implementação anterior, sem essa LRU.

Cinco testes adicionais/33 subtests verificam ownership, fechamento, streams,
validação e equivalência com o snapshot próprio anterior. Em 27 composições de
polígonos com buracos, clipping, tracejados, transparência, círculos e textos,
variando fundo, escala e rotação, os pixels RGBA e os bytes PNG são idênticos.
O smoke Tk impede chamadas a `Image.save`/`Image.open` durante a abertura e
confere a liberação da imagem anterior. Nenhum desses testes usa Matplotlib.

## Experimento antes/depois

[100 DPI](performance/viewer-100.json) e [200 DPI](performance/viewer-200.json)
registram Windows/Python 3.14.4/Tk 8.6/Pillow 12.3.0, hashes das fontes e
ferramentas, amostras e contadores. São dois pares por caso, com ordem alternada
e **16 intérpretes novos, executados serialmente**. Ambos os modos importam as
mesmas implementações próprias; o modo anterior restaura os snapshots Tk/PNG
anteriores à extração do RGBA e à remoção da retenção inicial. Os sete estados
de cada caso têm pixels RGBA, itens/vértices, vistas, histórico e estado stale
idênticos nos quatro workers: **112 registros de operações**.

Há widgets e event loop Tk reais em janelas ocultas e entradas sintéticas.
Abertura inclui root/widgets/ícones/composição/raster/PhotoImage/canvas e
`update_idletasks`, mas exclui construção da Figure e carregamento dos dados.
As demais operações incluem composição/raster/atualização do canvas. Pan mede
uma prévia e a recomposição ao soltar, sem medir throughput de arrasto contínuo.
Resize inclui debounce de 180 ms e callback de espera de 200 ms. O caso atlas
tem múltiplos mapas; zoom/pan alteram o primeiro Axes.

As bases Natural Earth incluídas são generalizadas; os valores temáticos do
atlas são sintéticos. O experimento não usa uma base municipal detalhada e
não mede input físico, pintura visível do sistema, screenshots ou percepção
da latência pelo usuário.

Medianas em segundos da implementação RGBA registrada neste experimento:

| Caso | DPI | Canvas inicial | Abrir | Redesenhar | Zoom | Pan/soltar | Home | Resize | Editar título |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| São Paulo | 100 | 640 × 480 | 1.741 | 1.396 | 1.287 | 1.277 | 1.360 | 1.742 | 1.592 |
| Brasil | 100 | 640 × 480 | 5.542 | 4.996 | 5.046 | 5.041 | 5.058 | 5.306 | 4.886 |
| Atlas | 100 | 1200 × 800 | 8.525 | 7.529 | 7.766 | 7.158 | 7.194 | 7.915 | 7.456 |
| São Paulo | 200 | 1280 × 960 | 3.922 | 3.420 | 3.398 | 3.231 | 3.228 | 3.544 | 3.592 |

Comparação de duas operações, antes → depois, em segundos:

| Caso/DPI | Abrir | Redesenhar |
|---|---:|---:|
| São Paulo/100 | 1.760 → 1.741 | 1.376 → 1.396 |
| Brasil/100 | 5.943 → 5.542 | 4.918 → 4.996 |
| Atlas/100 | 8.033 → 8.525 | 7.304 → 7.529 |
| São Paulo/200 | 3.548 → 3.922 | 3.174 → 3.420 |

Os tempos variam nos dois sentidos. Estas amostras pequenas não permitem
declarar aceleração geral, significância estatística ou navegação fluida. A
remoção do codec e da cópia inicial reduz trabalho/retenção desnecessários,
mas a preparação e a cobertura raster Python continuam custosas.

## Memória do processo

Contadores Windows são lidos fora do trecho cronometrado. O pico é o high-water
mark acumulado do processo inteiro, incluindo Python, dados, buffers nativos
e Tk; não é pico isolado de uma etapa nem apenas de memória nativa. Hashes de
pixels são calculados por faixas após tempo/contador e podem influenciar picos
das etapas seguintes. Não há tracemalloc/profiling/sampler simultâneo.

Medianas em MiB, antes → depois:

| Caso/DPI | Working set após abrir | Maior pico observado na sequência | Working set após editar título | Working set após fechar |
|---|---:|---:|---:|---:|
| São Paulo/100 | 77.3 → 75.8 | 126.3 → 121.8 | 82.0 → 78.2 | 76.9 → 74.3 |
| Brasil/100 | 93.5 → 92.0 | 142.4 → 132.5 | 107.7 → 97.6 | 102.6 → 93.7 |
| Atlas/100 | 105.8 → 102.2 | 203.7 → 188.4 | 126.0 → 110.5 | 109.0 → 99.1 |
| São Paulo/200 | 90.5 → 86.0 | 212.1 → 205.5 | 96.7 → 90.3 | 78.1 → 76.0 |

O contador após fechar ainda inclui referências locais à Figure, à última
Scene e aos dados, além de memória que o alocador pode reter. Não representa
um processo sem mapas nem prova ausência geral de vazamentos. As reduções
locais não garantem limites em outras bases, máquinas ou plataformas.

## Reprodução e trabalho restante

```bash
python tools/benchmark_viewer.py --cases state brazil atlas --dpi 100 --repeats 2 --output viewer-100.json
python tools/benchmark_viewer.py --cases state --dpi 200 --repeats 2 --output viewer-200.json
python tools/smoke_viewer_tk.py --output viewer-tk-validation.json
```

Rodar sem outros testes/benchmarks intensivos simultâneos. Os snapshots em
`tools/baselines/viewer-raster-before` são código próprio de referência de
desenvolvimento, não backend alternativo ou dependência do wheel.

Ainda faltam localizar/reduzir o custo da cobertura e da recomposição,
ampliar culling/cache e medir uma base detalhada real. Também faltam pintura
visível/input nativo e resultados reais de outras plataformas. Este lote
avança o critério de desempenho da [0.2.0](release-0.2.md), sem declará-lo
concluído. Veja também [validação desktop](viewer-validation.md).

## Proveniência após alterações do viewer

As medidas acima são históricas. O código RGBA medido está preservado em
`tools/baselines/viewer-rgba-measured/`, com hashes conferidos contra os relatórios.
O viewer/núcleo atual recebeu mudanças de primeiro draw, dimensões/DPI, títulos,
séries/ciclos e estilos depois
do experimento. Não se atribuem estes tempos à implementação atual nem se
declara aceleração decorrente das novas mudanças.

O [lote municipal de cobertura](municipal-raster.md) traz uma comparação nova
antes/depois da rasterização de vistas ainda não cacheadas. Ele mede o renderer
direto e preservação de pixels; não mede pintura visível ou input físico.

O [pan com renderer real](pan-responsiveness.md) mede separadamente a versão
anterior, source atual, wheel atual e TkAgg. Coalescência antes da composição e
raster temporário diminuíram os travamentos; a referência ainda redesenha mais
quadros por segundo. Exportação e quadros finais mantêm a cobertura exata.
