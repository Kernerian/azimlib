# Desempenho de mapas completos

Medições locais em 2026-09-30, Python 3.14.4, Pillow 12.3.0.
Não são garantias de latência nem comparação de velocidade com Matplotlib.
O núcleo cartográfico, composição e cobertura raster continuam próprios.

As seções abaixo registram experimentos de exportação/composição. O viewer Tk
também tem agora [medições separadas de latência e memória](viewer-performance.md)
e encaminha RGBA diretamente ao display. As amostras locais preservam pixels e
vistas; não demonstram aceleração geral nem pintura visível/input físico.

## Etapas separadas a 100 DPI

Medianas de duas amostras por etapa, em segundos. Composição é a construção
da Scene; SVG é serialização em memória; PNG inclui raster e encoding.
Setup/carregamento e a primeira composição estão registrados nos JSONs.
O atlas tem 12×8 polegadas; os outros casos, 6,4×4,8. Os pontos são sintéticos.

| Mapa | Composição | SVG | PNG | Zoom + recomposição | Pico Python da composição (MiB) |
|---|---:|---:|---:|---:|---:|
| São Paulo | 0,374 | 0,049 | 1,684 | 0,374 | 4,53 |
| Brasil | 0,621 | 0,084 | 5,742 | 0,735 | 7,27 |
| Atlas com spans | 1,261 | 0,146 | 9,181 | 1,275 | 14,28 |
| 1.500 pontos | 0,387 | 0,065 | 2,043 | 0,355 | 4,86 |

O pico de memória usa tracemalloc em uma passagem **separada**, somente
durante a composição Python. Não inclui leitura inicial dos dados, buffers
nativos de Pillow, memória residente do processo ou o total necessário para PNG.
Zoom mede Python sobre um Axes; exclui event loop, arraste, pintura Tk e browser.
Os caches de dados/fontes permanecem no processo: setup não é cold start independente.

## Comparação alternada do renderer

Quatro pares por mapa sobre a mesma Scene, alternando a ordem antes/depois.
Sem profiler ou tracemalloc durante as amostras. A comparação inicial em
processos separados apresentou variação, inclusive uma piora no atlas;
a comparação alternada abaixo é a evidência mais controlada para esta alteração.
Medianas em segundos, incluindo PNG encoding.

| Mapa | Antes | Depois | Redução observada | PNG idêntico |
|---|---:|---:|---:|---|
| São Paulo | 1,620 | 1,608 | 0,8% | sim, SHA-256 |
| Brasil | 5,909 | 5,834 | 1,3% | sim, SHA-256 |
| Atlas com spans | 8,799 | 8,168 | 7,2% | sim, SHA-256 |
| 1.500 pontos | 2,203 | 2,004 | 9,0% | sim, SHA-256 |

Os ganhos são modestos. Diferenças próximas de 1% podem ser ruído da máquina;
essa amostra pequena não estabelece significância estatística ou aceleração geral.
As imagens dos quatro casos ficaram byte a byte iguais. Isso não garante equivalência
para todos os estilos, tamanhos e cenas; há também regressões de cobertura/alpha.

As alterações reutilizam amostras angulares exatas de círculos (cache limitado),
tabelas de alpha por desenho (máximo 128) e evitam reclipping de um fragmento
que já cabe completamente em uma coluna de pixel. Não quantizam coordenadas,
não reduzem DPI, não simplificam geometria e não desligam antialiasing.

## Conferência em 200 DPI

São Paulo: 1280×960 pixels; composição 0,332 s, PNG 3,978 s.
Dois pares alternados: 3,691 → 3,727 s.
O PNG permaneceu idêntico; a amostra também é pequena. Não foi validado um atlas
completo em todos os DPI nem todos os componentes contra Agg nesta etapa.

## Reproduzir

Na pasta do projeto, com Pillow instalado:

```bash
python tools/benchmark_maps.py --repeats 3 --dpi 100 --memory --output maps.json
python tools/benchmark_maps.py --cases state --dpi 200 --repeats 3 --output state-200.json
python tools/compare_raster_versions.py --repeats 4 --output comparison.json
python tools/compare_composition.py --repeats 4 --output composition.json
```

Flags opcionais: `--profile-dir profiles` executa uma passagem adicional com
cProfile; `--preview-dir previews` salva os PNG/SVG medidos fora do intervalo
cronometrado. `--cases` seleciona mapas; `--points` muda a carga de scatter.
O comparador usa snapshots confiáveis do renderer anterior em
`tools/baselines/raster-before`, carregados serialmente apenas no tool de desenvolvimento.
Esses snapshots não entram no wheel nem no runtime da biblioteca.

Relatórios brutos: [etapas antes](performance/maps-before.json),
[etapas depois](performance/maps-after.json),
[comparação alternada](performance/renderer-comparison.json),
[estado 200 DPI](performance/state-200.json) e
[comparação 200 DPI](performance/renderer-comparison-200.json).
Incluem dimensões, primitivas, vértices, bytes, amostras e versões; o comparador
registra também SHA-256 dos fontes e dos PNGs.

## Cache do viewport e descarte conservador — composição

Quatro passagens alternadas de cada modo, a 100 DPI. A referência é o viewport
anterior da própria Azimlib, sem cache; todos os modos usam os bounds imutáveis
atuais. Cache completo mantém todas as geometrias; cache + descarte omite somente
linhas/polígonos certamente invisíveis em Mercator/equiretangular.

| Mapa | Referência própria (s) | Cache completo (s) | Cache + descarte (s) | Redução na composição | PNG idêntico |
|---|---:|---:|---:|---:|---|
| São Paulo | 0,375 | 0,351 | 0,120 | 68,1% | sim, SHA-256 |
| Brasil | 0,648 | 0,589 | 0,496 | 23,5% | sim, SHA-256 |
| Atlas com spans | 1,289 | 1,090 | 0,678 | 47,4% | sim, SHA-256 |
| 2.501 polígonos sintéticos | 0,222 | 0,191 | 0,038 | 82,7% | sim, SHA-256 |

Composição inclui layout e produção da Scene. PNG foi renderizado depois das
amostras, uma vez por modo, para igualdade byte a byte. O JSON também registra
recomposição após zoom, número de primitivas e todas as amostras. No caso
sintético, a cena cai de 2.535 para 58 primitivas; não são limites municipais reais.
As diferenças de cache isolado são menores e a amostra é curta; os resultados
não garantem aceleração geral. Não foram medidos tempo raster alternado, RSS,
buffers nativos ou resposta real da GUI nesta comparação.

O HTML continua com todas as geometrias para pan; apenas limites projetados são
reutilizados. Nenhum ornamento passa a ser obrigatório. Consulte o
[contrato e limites](viewport-performance.md) e o
[relatório bruto](performance/composition-comparison.json).

## Gargalos e próximo trabalho

O profiler ainda concentra tempo em stroke/coverage, clipping por pixel e
preenchimentos. Composição do atlas também importa para navegação. Continuam
pendentes ampliação do culling/índice espacial e do cache para outras camadas,
fronteiras compartilhadas,
simplificação com erro visual controlado e renderização incremental. Não se
declara navegação fluida de municípios detalhados, suporte a GPU ou encerramento
do critério de desempenho da versão 0.2.0.

## Índice espacial — consultas reutilizadas

Seis pares alternados, a 100 DPI, comparando descarte linear e consulta ao BVH.
Os dois modos usam o mesmo cache de viewport e o mesmo descarte conservador.
A construção inicial do índice foi medida **antes**, fora das composições abaixo.
As primitivas/metadados e os PNGs dos cinco casos foram idênticos.

| Caso | Varredura (s) | Índice preparado (s) | Variação observada |
|---|---:|---:|---:|
| São Paulo | 0,124 | 0,118 | −5,2% |
| Brasil | 0,459 | 0,479 | +4,4% |
| Atlas | 0,651 | 0,653 | +0,4% |
| 2.501 polígonos sintéticos | 0,039 | 0,007 | −83,0% |
| 20.000 polígonos sintéticos | 0,280 | 0,013 | −95,3% |

São Paulo e atlas não têm coleções elegíveis neste benchmark: suas variações
não são ganhos atribuíveis ao índice. Brasil tem uma coleção de 177 países;
o resultado foi um pouco mais lento. A amostra curta/variação da máquina não
estabelecem significância estatística. O ganho expressivo observado foi nas
duas bases sintéticas, com muitas features fora da vista.

| Coleção | Preparação inicial (s) | Alocação retida do novo índice (MiB) | Pico de preparação (MiB) |
|---|---:|---:|---:|
| 177 países | 0,014 | 0,03 | 0,05 |
| 2.501 polígonos | 0,059 | 0,84 | 1,04 |
| 20.000 polígonos | 0,519 | 6,48 | 11,31 |

A preparação de 20.000 polígonos custa mais que uma varredura. Ela é amortizada
por consultas futuras; **uma primeira exportação pode ser mais lenta**. Os
limites/geometrias já carregados são compartilhados com uma coleção nova na
medição de memória, realizada separadamente com tracemalloc. Retido/pico contam
alocações Python do índice, não memória dos dados, bounds existentes, RSS,
buffers nativos ou renderer. O cache retém até quatro projeções por coleção.

Zoom + recomposição reutilizada passou de 0,270 para 0,009 s no caso de 20.000
polígonos. Isso exclui event loop, rasterização e pintura: não é uma medição
de latência do viewer. Não é uma base municipal real, nem uma comparação com
Matplotlib. Veja [contrato do índice](spatial-index.md) e
[amostras brutas](performance/spatial-index.json).

```bash
python tools/benchmark_spatial.py --repeats 6 --memory --output spatial.json
```

Próximos trabalhos: ampliar
consultas para labels/campos e outras projeções, ampliar o cache de vértices e
validação com bases reais/GUI funcional. A estrutura atual não é simplificação,
topologia ou aceleração GPU.

## Preparação compacta — BVH anterior versus STR atual

Seis pares alternados com índices novos, compartilhando os mesmos dados e bounds
já aquecidos. A referência é o snapshot próprio anterior; o novo índice agrupa
caixas em faixas STR e guarda os envelopes em bytes float64 imutáveis. Mantém
precisão, API e ordem das chaves. As consultas, primitivas/metadados e PNGs
dos dois mapas sintéticos foram iguais. Esta medição substitui apenas o índice,
sem mudar o renderer e sem comparar com Matplotlib.

| Polígonos sintéticos | Preparação anterior → atual (s) | Python retido anterior → atual (MiB) | Pico anterior → atual (MiB) |
|---|---:|---:|---:|
| 2.501 | 0,046 → 0,039 | 1,06 → 0,50 | 1,33 → 0,89 |
| 20.000 | 0,410 → 0,348 | 6,51 → 2,11 | 11,60 → 10,43 |

Com 20.000 polígonos, a preparação foi 15,1% mais rápida e o índice retido
ocupou 67,5% menos alocação Python nesta execução. O pico caiu menos, 10,1%:
a validação e os envelopes temporários ainda têm custo. Retido/pico excluem
geometrias/bounds existentes, memória nativa/RSS e rasterização. Não devem ser
interpretados como consumo total do aplicativo.

| Coleção / consulta | Anterior → atual | Candidatos |
|---|---:|---:|
| 2.501 / foco regional | 18,4 → 18,9 µs | 24 |
| 20.000 / foco regional | 64,8 → 74,7 µs | 108 |
| 2.501 / caixa inteira | 0,801 → 0,100 ms | 2.501 |
| 20.000 / caixa inteira | 13,841 → 2,502 ms | 20.000 |

Consultas que contêm a caixa total retornam as chaves sem testar cada envelope;
folhas totalmente contidas também dispensam desempacotamento. A consulta focada
de 20.000 caixas ficou cerca de 10 µs mais lenta (15,3%) nesta amostra: compactar
não garante ganho em toda consulta. A medição anterior de composição linear/BVH
acima é histórica, não uma medição de composição ou GUI do STR atual.

```bash
python tools/compare_spatial_builders.py --repeats 6 --output builders.json
```

O [relatório bruto](performance/spatial-builders.json) registra amostras, versões,
SHA-256 dos fontes e PNGs. Alocações e pintura ficam fora do cronômetro.
Permanece custo na primeira preparação; limites municipais reais, outras
projeções/camadas, memória nativa e latência desktop ainda precisam de validação.

## Cache de paths — composição e zoom

Seis pares alternados a 100 DPI, comparando o compositor de geometria anterior
da própria Azimlib com o atual. Viewport, índice, estilos, layout e renderer
são os mesmos. As cinco cenas e PNGs ficaram idênticos por SHA-256.

| Mapa | Composição anterior → aquecida (s) | Zoom anterior → aquecido (s) | Primeira composição anterior → atual (s) |
|---|---:|---:|---:|
| São Paulo | 0,115 → 0,017 | 0,111 → 0,017 | 0,121 → 0,128 |
| Brasil | 0,499 → 0,040 | 0,487 → 0,036 | 0,537 → 0,584 |
| Atlas | 0,681 → 0,051 | 0,695 → 0,062 | 0,720 → 0,704 |
| 2.501 polígonos sintéticos | 0,007 → 0,006 | 0,007 → 0,004 | 0,007 → 0,009 |
| Globo ortográfico | 0,149 → 0,004 | 0,149 → 0,004 | 0,144 → 0,152 |

Há ganhos expressivos na composição aquecida dos mapas generalizados, ao evitar
recortar/densificar/projetar os mesmos vértices. Na malha sintética, o índice já
seleciona poucos polígonos simples e o ganho absoluto é pequeno. A primeira
composição sem cache de vértices continua pagando a preparação: São Paulo,
Brasil, malha e globo ficaram mais lentos nesta execução; a diferença do atlas
é pequena e não estabelece ganho inicial. Dados/bounds/viewport/índice já estão
aquecidos em ambos os modos: não é início do processo ou custo de abrir os dados.

| Mapa | Payload retido (MiB) | Python retido após composição (MiB) | Pico da composição/preparação (MiB) |
|---|---:|---:|---:|
| São Paulo | 0,19 | 0,35 | 1,94 |
| Brasil | 0,83 | 1,04 | 7,17 |
| Atlas | 1,15 | 1,35 | 10,26 |
| Sintético | 0,006 | 0,06 | 0,10 |
| Globo | 0,14 | 0,44 | 1,43 |

Payload conta bytes/tuplas próprios do cache; o limite de 8 MiB/1.024 entradas
vale para esses dados retidos. Python retido/pico vêm de uma passagem separada
com tracemalloc que inclui cache e composição; não são só buffers do cache.
Excluem dados/bounds já existentes, memória nativa/RSS e PNG. O pico pode
ultrapassar o orçamento de retenção. Fontes são weakrefs; geometrias liberadas
não ficam presas ao cache. PNG foi pintado fora do cronômetro e continua usando
o mesmo renderer, com seus gargalos de rasterização. O ganho de composição não
significa o mesmo ganho no tempo total de savefig ou na resposta desktop.

```bash
python tools/compare_projected_paths.py --repeats 6 --output paths.json
```

O [relatório bruto](performance/projected-paths.json) inclui todas as amostras,
bytes/evicção, versões e hashes de fontes/PNGs. Veja [contrato do cache](projected-paths.md).
Esta entrega não mede GUI, não valida municípios detalhados e não fecha o
critério de desempenho 0.2. Simplificação, fronteiras compartilhadas, cache de
campos/labels e rasterização incremental/em lote continuam pendentes.


## Recortes de cobertura dispensados — consolidação em vários DPI

O perfil de mapas completos ainda aponta CoverageDraw/_clip como custo principal
da rasterização. Agora, quando todos os vértices já pertencem ao semiplano de
uma faixa/coluna, o renderer reutiliza a mesma sequência em vez de repetir o
recorte. Os demais recortes, área fracionária e desenho continuam iguais. Não
há quantização, redução de DPI, simplificação ou alteração de antialiasing.

Comparação serial alternada sobre a mesma Scene completa, com PNG encoding,
sem profiler/tracemalloc na medição: quatro pares por caso em 100 DPI e dois
em 200 DPI. O snapshot anterior é da própria Azimlib. Todos os PNGs foram
byte a byte iguais (SHA-256), junto das regressões de máscaras e estilos.

| Caso | DPI | Antes (s) | Depois (s) | Redução local | PNG idêntico |
|---|---:|---:|---:|---:|---|
| state | 100 | 1.619 | 1.508 | 6.9% | sim |
| brazil | 100 | 5.762 | 5.117 | 11.2% | sim |
| atlas | 100 | 8.588 | 8.140 | 5.2% | sim |
| state | 200 | 3.843 | 3.603 | 6.3% | sim |
| atlas | 200 | 15.734 | 14.548 | 7.5% | sim |

Os ganhos são modestos e variam entre mapas/DPI. Poucas amostras não estabelecem
significância estatística ou uma aceleração geral; event loop/pintura da GUI
não foram medidos. Dados brutos: [100 DPI](performance/coverage-clipping-100.json)
e [200 DPI](performance/coverage-clipping-200.json).

```bash
python tools/compare_raster_versions.py --baseline-dir tools/baselines/coverage-clipping-before --cases state brazil atlas --dpi 100 --repeats 4 --output clipping-100.json
python tools/compare_raster_versions.py --baseline-dir tools/baselines/coverage-clipping-before --cases state atlas --dpi 200 --repeats 2 --output clipping-200.json
```

## Memória de processo incluindo buffers nativos

Medição serial em um processo Python novo por mapa/DPI. No Windows,
GetProcessMemoryInfo registra working set corrente, seu pico e compromisso
privado do processo. Inclui runtime, dados, Python e buffers nativos do PNG;
não representa uma separação entre alocações Python e nativas. O pico é o
high-water mark do processo desde seu início, não uma diferença de alocação
em cada etapa. Working set é memória residente sujeita à política do OS;
compromisso privado não é o mesmo conceito. Não se subtrai um baseline.

| Caso | DPI | Working set após PNG (MiB) | Pico do processo (MiB) | Compromisso privado após PNG (MiB) |
|---|---:|---:|---:|---:|
| state | 100 | 55.47 | 89.39 | 46.22 |
| state | 200 | 55.45 | 199.99 | 46.04 |
| brazil | 100 | 70.30 | 95.66 | 60.66 |
| brazil | 200 | 73.26 | 187.12 | 64.29 |
| atlas | 100 | 73.64 | 155.13 | 64.88 |
| atlas | 200 | 78.33 | 403.46 | 69.83 |

O atlas em 200 DPI chegou a cerca de 403 MiB de pico neste ambiente. O canvas
interno de supersampling e tiles/máscaras/cores temporários ainda importam;
essa medição torna explícito um custo que tracemalloc não cobria. Não é um
limite garantido de memória nem uma medição de uso durante navegação desktop.
A comparação nativa possui uma execução por caso; ampliar amostras/cenários
e reduzir buffers temporários continuam pendentes.

O [relatório bruto](performance/process-memory.json) contém etapas após imports,
dados/Artists, Scene e PNG, dimensões e fonte dos contadores. Usou cull=True;
a comparação alternada de renderer acima conserva a Scene completa. Unix tem
fallback de pico RSS via resource; só a execução Windows foi verificada aqui.

```bash
python tools/measure_process_memory.py --cases state brazil atlas --dpi 100 200 --output process-memory.json
```

Veja também as [nove comparações visuais de mapas completos](complete-map-quality.md).
A qualidade/desempenho da 0.2.0 ainda exigem validações adicionais; essas entregas
não encerram os critérios nem adicionam expansões urbanas/3D antes do corte.

## Reutilização e liberação de buffers PNG

O primeiro paint de uma geometria reutiliza seu tile RGBA transparente: escreve
a cor e copia a cobertura alpha, sem alocar outra imagem RGBA nem compor com
um destino vazio. Preenchimento/traço subsequentes ainda usam composição alpha;
textos mantêm esse caminho antes de rotação e filtragem. Máscaras, cores,
bandas alpha e tiles próprios são liberados logo após uso, evitando que o item
anterior retenha buffers grandes durante a alocação do próximo. Supersampling
3x, BOX, cobertura, geometria, DPI e fontes continuam iguais.

As regressões confrontam um snapshot anterior próprio, incluindo fundos
transparentes/coloridos, buracos, cores RGBA, alpha global, traços/tracejados,
recortes fracionários e textos intercalados com halo, fundo e rotação em três
resoluções. Conferem também menor volume alocado em buffers RGBA, liberação
antes do encoding mesmo com referências aos objetos retidas pelo teste e
streams pertencentes ao chamador, inclusive após falha de escrita.

A comparação de tempo usa a mesma Scene completa e PNG encoding, em pares
alternados, sem medidor de memória/profiler/cargas concorrentes. A comparação
de memória é separada: cada modo/mapa/DPI/amostra inicia um intérprete novo,
ambos carregam os mesmos módulos antes de selecionar o renderer e usam
cull=True. Os contadores Windows cobrem o processo inteiro desde o início,
incluindo runtime/dados/Python/buffers nativos. Não são um pico exclusivo do
PNG nem uma subtração de baseline. Working set, seu pico e compromisso privado
são conceitos distintos; poucos pares não definem um limite geral ou ganho
estatisticamente comprovado. Navegação desktop/GUI não foi medida.

| Caso | DPI | Antes (s) | Depois (s) | Redução local | PNG idêntico |
|---|---:|---:|---:|---:|---|
| state | 100 | 1.561 | 1.538 | +1.5% | sim |
| brazil | 100 | 5.159 | 5.148 | +0.2% | sim |
| atlas | 100 | 7.667 | 7.787 | -1.6% | sim |
| state | 200 | 3.627 | 3.675 | -1.3% | sim |
| atlas | 200 | 15.207 | 14.636 | +3.8% | sim |

Tempo praticamente estável neste conjunto: há pequenas melhoras e regressões,
sem aceleração geral declarada. Sinal negativo na coluna de redução significa
mais tempo. São quatro pares em 100 DPI e dois em 200 DPI. O atlas a 100 DPI
foi repetido sozinho após as verificações, descartando a execução que coincidiu
com testes. Dados: [100 DPI](performance/raster-buffers-100.json),
[repetição do atlas](performance/raster-buffers-atlas-100.json) e
[200 DPI](performance/raster-buffers-200.json). Todos preservaram os bytes PNG.

| Caso | DPI | Pico antes (MiB) | Pico depois (MiB) | Redução local | PNG idêntico |
|---|---:|---:|---:|---:|---|
| state | 100 | 89.69 | 87.59 | 2.3% | sim |
| state | 200 | 200.22 | 192.12 | 4.0% | sim |
| brazil | 100 | 97.04 | 96.82 | 0.2% | sim |
| brazil | 200 | 187.79 | 182.20 | 3.0% | sim |
| atlas | 100 | 155.51 | 155.14 | 0.2% | sim |
| atlas | 200 | 403.32 | 401.34 | 0.5% | sim |

Medianas de dois pares por caso/DPI, 24 workers novos e 96 registros de etapas.
O [relatório de memória](performance/raster-buffers-memory.json) conserva todas
as amostras, hashes do renderer/PNG, dimensões, working set/compromisso privado
correntes e pico do processo. Aqui o ganho de pico é modesto e não é uniforme:
reduzir os temporários dos itens não resolve o pico alto do atlas em 200 DPI,
que permanece em cerca de 401 MiB. O canvas supersampled e os buffers da redução
final são os próximos candidatos a investigar; esta medição por etapas não
localiza o instante do pico dentro do renderer. Diferenças pequenas estão sujeitas
à variação do OS; não se usa a medição histórica de 403,46 MiB como baseline
deste experimento. Ainda reduzir buffers do canvas/redimensionamento, ampliar
amostras e validar GUI/bases detalhadas; este resultado não fecha a 0.2.0.

```bash
python tools/compare_raster_versions.py --baseline-dir tools/baselines/raster-buffers-before --cases state brazil atlas --dpi 100 --repeats 4 --output buffers-100.json
python tools/compare_raster_versions.py --baseline-dir tools/baselines/raster-buffers-before --cases state atlas --dpi 200 --repeats 2 --output buffers-200.json
python tools/compare_raster_memory.py --cases state brazil atlas --dpi 100 200 --repeats 2 --output buffers-memory.json
```

## Canvas: composição e redução BOX em faixas

O diagnóstico de um atlas em 200 DPI registra aumento de memória durante a
conversão RGBA → RGBa que o Pillow faz antes de filtrar alpha, seguido de
redimensionamento e retorno para RGBA. É uma passagem instrumentada para
localizar candidatos, separada das amostras de tempo/memória: callbacks não
observam cada alocação transitória dentro das operações nativas e seu pico
continua sendo do processo inteiro.

A composição de tiles grandes agora usa faixas de linhas. Alpha composition
é independente por pixel, portanto cada faixa preserva a operação anterior
sem criar cópias completas do destino e resultado do tile. Tiles pequenos
mantêm o caminho anterior; fill/stroke/texto continuam com as mesmas regras.

A redução final também usa faixas: o canvas tem exatamente três pixels fonte
em cada dimensão por pixel de saída. No filtro BOX cada linha de saída utiliza
suas três linhas fonte, sem precisar sobrepor faixas. Cada crop ainda passa
pelo resize RGBA normal do Pillow, com alpha premultiplicado e os mesmos dois
passos de filtragem/arredondamento. Não há filtro novo, redução de DPI,
atalho apenas para fundo opaco ou alteração de geometria/textos. A saída segue
RGBA, com as mesmas dimensões/bytes PNG do renderer próprio anterior.

As faixas são usadas para fontes RGBA acima de 16 MiB. Abaixo disso, o caminho
integral anterior evita crops extra e a sobrecarga de novos tamanhos de buffers.
Quando as faixas são usadas, cada crop próprio tem orçamento de 4 MiB. Ele exige pelo menos uma linha
inteira na composição, ou três linhas fonte na redução BOX; uma imagem
extremamente larga pode ultrapassar esse orçamento mínimo. Há outros buffers
simultâneos (canvas, tile, masks, resultado, conversão/filtro do Pillow). Esse
orçamento não limita a memória do renderer nem do processo inteiro, e o canvas
supersampled completo ainda existe.

Oito regressões comparam RGBA aleatório, alpha extremo/RGB invisível, linhas
alternadas, divisões entre faixas e última faixa parcial, composição em offsets,
orçamento menor que uma linha, limpeza após erro e entradas emprestadas
inalteradas e caminho pequeno sem crops próprios. PNGs completos com texto rotacionado/halo/fundo, buracos, traços,
recortes e quatro fatores de resolução confrontam o snapshot próprio anterior.

| Caso | DPI | Antes (s) | Depois (s) | Redução local | PNG idêntico |
|---|---:|---:|---:|---:|---|
| state | 100 | 1.494 | 1.462 | +2.1% | sim |
| brazil | 100 | 5.778 | 5.917 | -2.4% | sim |
| atlas | 100 | 7.324 | 7.228 | +1.3% | sim |
| state | 200 | 3.238 | 3.405 | -5.2% | sim |
| atlas | 200 | 15.221 | 15.565 | -2.3% | sim |

Quatro pares por caso em 100 DPI e dois em 200 DPI, serialmente na mesma Scene
completa com PNG encoding. Sinal negativo representa mais tempo; não há ganho
geral de velocidade e a menor memória tem custo de crops/chamadas adicionais
nos buffers grandes. As amostras locais pequenas não estabelecem significância
estatística. Dados: [100 DPI](performance/raster-bands-100.json) e
[200 DPI](performance/raster-bands-200.json), com versões, hashes e todas as
amostras. Nenhuma medição de GUI está incluída.

| Caso | DPI | Pico antes (MiB) | Pico depois (MiB) | Redução local | PNG idêntico |
|---|---:|---:|---:|---:|---|
| state | 100 | 87.76 | 87.41 | +0.4% | sim |
| state | 200 | 192.01 | 156.17 | +18.7% | sim |
| brazil | 100 | 96.91 | 97.30 | -0.4% | sim |
| brazil | 200 | 181.93 | 166.65 | +8.4% | sim |
| atlas | 100 | 154.89 | 135.52 | +12.5% | sim |
| atlas | 200 | 401.10 | 288.08 | +28.2% | sim |

Medianas de dois pares por caso/DPI, 24 workers novos, 96 registros de etapas,
sem Matplotlib/GIS. O [relatório de memória](performance/raster-bands-memory.json)
contém todos os contadores, metadata e hashes. Cada worker carrega ambos os
renderers e constrói o mesmo mapa com cull=True; pico é do processo inteiro
desde o início, incluindo runtime/dados/Python/buffers nativos, sem subtração
de baseline. Amostras pequenas/variação do OS limitam a interpretação. Em
100 DPI São Paulo/Brasil conservam o caminho integral e o pico varia pouco;
o ganho é mais claro nos buffers grandes, sem garantia geral de limite/latência.

Os diagnósticos separados [antes](performance/raster-bands-diagnostic-before.json)
e [depois](performance/raster-bands-diagnostic-after.json) registram chamadas
grandes de resize/composição e picos acumulados. Não entram nas medianas de
tempo/memória acima. O orçamento de faixas não elimina o canvas completo nem
tiles/máscaras grandes, e não localiza cada pico transitório nativo. Mais
cenários, GUI, caches/cobertura e validação de plataformas seguem pendentes.

```bash
python tools/compare_raster_versions.py --baseline-dir tools/baselines/raster-box-before --cases state brazil atlas --dpi 100 --repeats 4 --output bands-100.json
python tools/compare_raster_versions.py --baseline-dir tools/baselines/raster-box-before --cases state atlas --dpi 200 --repeats 2 --output bands-200.json
python tools/compare_raster_memory.py --baseline-dir tools/baselines/raster-box-before --cases state brazil atlas --dpi 100 200 --repeats 2 --output bands-memory.json
python tools/diagnose_raster_memory.py --baseline-dir tools/baselines/raster-box-before --case atlas --dpi 200 --output diagnostic-before.json
python tools/diagnose_raster_memory.py --case atlas --dpi 200 --output diagnostic-after.json
```


## Aritmética da cobertura dos traços

A cobertura exata continua calculando a interseção do polígono de traço com
cada pixel. O recorte escolhe o sentido do semiplano uma vez por chamada,
evitando uma condição repetida por vértice. O cálculo de área ganhou caminhos
para três e quatro vértices, reutilizando deltas sem generator/zip/slices.
Todos os termos, inclusive os termos zero e de fechamento, sua ordem e o uso
de `sum` foram preservados; não se altera arredondamento, geometria, DPI ou AA.

Um [diagnóstico não cronometrado](performance/stroke-area-counts.json) do atlas
em 100 DPI contou 567.653 chamadas com três/quatro vértices. Essa contagem
orientou a mudança; não mede duração nem a distribuição em outros mapas.

Quatro regressões adicionais (3.041 subtests) confrontam o snapshot próprio
anterior: bits dos floats de áreas/coordenadas recortadas, ordem dos vértices,
entradas preservadas, máscaras individuais/acumuladas e PNGs completos com
caps/junções/tracejados/alpha/buracos/texto/clipping em três resoluções.

| Caso | DPI | Antes (s) | Depois (s) | Redução local | PNG idêntico |
|---|---:|---:|---:|---:|---|
| state | 100 | 1.303 | 1.185 | 9.1% | sim |
| brazil | 100 | 4.322 | 4.037 | 6.6% | sim |
| atlas | 100 | 6.398 | 5.937 | 7.2% | sim |
| state | 200 | 3.105 | 2.691 | 13.3% | sim |
| atlas | 200 | 12.679 | 11.451 | 9.7% | sim |

Medianas de quatro pares por caso em 100 DPI e dois em 200 DPI. Os modos foram
alternados serialmente na mesma Scene, incluindo codificação PNG, sem profiling
ou instrumentação de memória simultânea. Todos os hashes PNG coincidiram.
Dados: [100 DPI](performance/stroke-arithmetic-100.json),
[200 DPI](performance/stroke-arithmetic-200.json), com versões/fontes/amostras.

Reduções locais de 6,6% a 13,3% nestas amostras pequenas não são garantia geral
de velocidade/significância estatística. Não se mediu latência GUI ou novo pico
de memória deste lote; os resultados anteriores de memória se referem às
versões e experimentos das seções anteriores. Canvas completo, bases densas,
mais plataformas/GUI e custo de preparação/cobertura ainda exigem trabalho.

```bash
python tools/compare_raster_versions.py --baseline-dir tools/baselines/stroke-arithmetic-before --cases state brazil atlas --dpi 100 --repeats 4 --output stroke-100.json
python tools/compare_raster_versions.py --baseline-dir tools/baselines/stroke-arithmetic-before --cases state atlas --dpi 200 --repeats 2 --output stroke-200.json
```

## Aceite local do passo 4

Os registros acima são experimentos históricos, com os hashes dos respectivos módulos. O [aceite atual](performance-acceptance.md) acrescenta a malha original SP (892.336 posições), mesh/contorno/scatter, oito pares finais RGBA/PNG idênticos, kernels próprios compiláveis opcionais e input humano em janela visível. O cache atual de paths tem 16 MiB de payload. Raster preciso reduziu localmente 42–63%, com memória maior; primeira vista densa continua lenta. A aceitação explicita limites e não declara CI multiplataforma concluída.
