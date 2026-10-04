# Verificação desta entrega

> Evidência histórica: resultados CI, tempos e hashes abaixo pertencem aos
> snapshots originais. A preparação BSD/licenças/privacidade altera arquivos;
> os checks atuais e a relação de hashes publicados estão em
> [preparação de publicação](publication-readiness.md). Esses resultados não são uma nova execução CI.

## Lote final local 5.08–5.09

[Auditoria de distribuição e instalação](distribution-acceptance.md) e [resultados retidos](release-validation-local.json): duas suítes inteiras instaladas, kernel opcional, core offline e 13 scripts Tk por Python 3.11/3.14. Deadline inicial excedido em layout e retry ficam separados; não se soma repetição como teste novo. Runtime preservado. 49 dos 54 IDs concluídos; CI real e conferência nativa Linux/macOS ainda pendentes. [Preparar GitHub usando Windows](ci-setup.md).

- Python 3.14.4, Windows; Matplotlib 3.11.2 em ambiente de referência separado.
- 675 testes passaram, com 22.192 subtests, em 187,385 s, incluindo compilador opcional: matemática, dados, composição, estilos,
  componentes, navegação, renderizadores e independência do pacote.
- Toolbar Tk comparada à referência instalada em quatro escalas físicas:
  Checkbuttons Pan/Zoom, dimensões e cursor corrigidos. A revisão inclui hover plano, nomes opcionais, ícones originais da Azimlib em
  desktop/HTML e editor Subplots ttk, baseado na organização do diálogo Qt.
  Sete regressões/23 subtests naquele lote; 28 checks Tk atuais source/wheel, baselines
  regenerados e integração instalada repetida. [Evidências](toolbar.md).
  Isso não substitui a inspeção visível exigida em 3.08–3.10.
- Corrigidos os problemas de organização no grupo Subplots, tooltip
  e arrasto. [Pan ao vivo](pan-interaction.md): 60 gestos diretamente comparados
  à referência, regressões de gesto contínuo/release perdido e onze checks Tk por instalação.
  Ticks/limites mudam enquanto o botão permanece pressionado, moldura fixa e
  release sem salto. Não se declara latência física equivalente.
- Responsividade medida com renderer real, source/wheel e TkAgg: coalescência
  antes da composição, tiles próprios e processo de pixels genéricos substituem
  a integração precisa durante o gesto, mantendo o quadro final/exportação
  exatos. Source/wheel: 30,90/31,99 quadros/s neste exemplo; primeira pegada/retomada
  instaladas: 39/46 ms. Regressões cobrem espessura em 16 ângulos/larguras, texto,
  cache/cancelamento/fechamento do subprocesso e release perdido nas bordas.
  A verificação visual Windows cobre espessura, componentes e continuidade do pan. Handler atual ~2 ms,
  coordenadas conferidas em seis casos. [Tempos e limitações](pan-responsiveness.md).
- Ícones copiados e suas licenças removidos na atualização da toolbar;
  geometria original compartilhada entre RGBA/SVG, bordas antialiasadas e
  transparência própria. Cinco regressões para assets/hash, SVG sem dependências,
  simetria e pequenos tamanhos; auditoria de arquivos/HTML e distribuições.
  [Proveniência própria](toolbar-icons-audit.json).
- Rotação conferida em 768 caixas Matplotlib/Agg e 1.536 planos Python/JavaScript;
  modos default/anchor/xtick/ytick em ticks e textos de mapa, Figure e componentes.
  Matriz de 24 cenas e seis conjuntos PNG/SVG/HTML regenerados; 16 regressões
  novas, também aprovadas no wheel. [Regras](text-rotation.md) e
  [casos/limites](layout-acceptance.md).
- Baselines finais e documentação do corte: [19 exemplos/38 cenas](release-gallery.md)
  em 100/200 DPI; 19 reproduções idênticas em PNG/SVG/HTML no wheel instalado,
  oito pares de Axes nativos Matplotlib e cinco pares same-Scene/Agg. Textos
  SVG/XML e recortes conferidos, zero texto livre fora do canvas nesses casos.
  117 regressões/2.696 subtests repetidos, sem falhas; não aumenta a suíte total.
  [Guia inicial executável](getting-started.md), referência de API regenerada,
  alvos locais Markdown auditados e nove execuções dos três snippets, source,
  core novo sem dependências opcionais e GUI instalado, com SVGs idênticos.
  [Relatório](documentation-check.json) e [diferenças/limites](visual-differences.md).
  A observação visual Windows está separada dos smokes e métricas automatizados no registro 3.08.
- Checklist 0.2.0: 54 IDs auditáveis, 47 concluídos/sete abertos (um aceite),
  passos 1–4 aceitos no escopo. Layout: 24 cenas, 30 checks/18 frames Tk
  source/wheel; nove scripts anteriores repetidos no wheel, além do smoke de
  Artists novamente source/wheel (14 checks). [Aceite do passo 2](layout-acceptance.md).
  Registro do passo 1:
  com passo 1/Artists aceito no catálogo: 1.08–1.12 encerrados.
  Dez novas regressões/118 subtests; seis mappables, 28 handles auditados,
  PNG/SVG e 14 checks Tk source/wheel. Referência instalada de aliases e três
  vistas manuais de imshow; normas de choropleth prevalidas, alinhamento/ticks
  e estilos incompatíveis de texto rejeitados antes de editar estado.
  [Aceite e limites](artist-acceptance.md). A 0.2.0 ainda não está pronta.
- Passo 4 encerrado localmente: base original SP/IBGE de 892.336 posições,
  mesh/contorno/scatter, oito pares finais RGBA/PNG idênticos e redução local
  de 42–63% no raster com compilador opcional próprio. Composição de pan novo
  de 9,09 para 0,41 s, sem cache de imagem. Memória maior/custo frio/pausas
  densas explícitos em [medições e limites](performance-acceptance.md).
  A execução visual Windows da janela Brasil registrou: 1.606 eventos nativos/246
  pinturas idle; não mede latência do monitor. Sessão pesada por API tem
  canvas mapeado nas duas mudanças e não é input humano.
  39 testes selecionados no wheel com compilador e os mesmos 39 sem ele
  (dois checks exclusivos do compilador pulados); onze checks Tk de pan
  novamente source e wheel. Núcleo instalado offline em ambiente novo
  sem opcionais/Matplotlib/GIS; 19 exemplos e nove snippets reproduzidos.
  [Auditoria das evidências](performance-acceptance-audit.json).
- Revisão anterior de contornos 1.09:
  Sete novas regressões/44 subtests e dez casos de referência Agg; campos
  constantes editáveis, lacunas, níveis/precisão, normas e PNG/SVG em 100/200 DPI.
  [Escopo e diferenças](contour-boundaries.md). A checklist não declara 0.2.0 pronta.
- Kernels/linhas coincidentes: oito regressões/5.887 subtests adicionais;
  18 casos de visibilidade Agg registrados, onze cenários/44 renders próprios
  em 100/200 DPI e 12 novas verificações Tk source/wheel. Os oito scripts Tk
  anteriores passaram novamente no wheel; [escopo e limites](stroke-kernels.md).
- Cobertura municipal: quatro regressões/1.087 subtests adicionais de bits de
  área, máscaras e PNG. Quatro vistas/16 renders source preservaram RGBA/PNG;
  oito scripts Tk passaram novamente com o wheel instalado. Comparador e
  limites de desempenho estão [documentados](municipal-raster.md).
- Lote maior: 21 regressões/61 subtests adicionais em aliases, cache e composição
  integrada; 13 pares de aliases registrados do Matplotlib, 12 cenários de
  tamanho/DPI/orientação e oito verificações Tk source/wheel. As 54 composições
  anteriores permanecem verificadas. Medição de 645 municípios/222.324 posições
  da API IBGE preservou cenas/PNG em quatro vistas e histórico no Tk instalado.
  [Relatórios e limites](larger-batch.md), incluindo rasterização inicial ainda lenta.
- Auditoria de Artists: 12 regressões/52 subtests adicionais, estados de setters
  registrados em Matplotlib e sete verificações integradas Tk source/wheel.
  Falhas preservam estado/desenho; números e tracejados válidos permanecem
  renderizáveis. Veja [escopo e diferenças](artist-validation.md).
- Lote de texto/formatação: 18 regressões/132 subtests; métricas verticais em toda
  a base de texto, 96 caixas comparadas diretamente a Agg, onze marcadores,
  notação científica/offsets/prefixos SI, quatro posições de colorbar e dez
  cenários Tk novos. Matriz de 54 composições recalculada após alteração
  intencional das caixas da fonte: zero overflow próprio nas medidas registradas.
  Veja [evidências e limites](numeric-formatting.md).
- Acabamento dos frames: três regressões/54 subtests adicionais para texto
  editado/multilinha na legenda, margens verticais/contenção da escala e 16
  dimensões de colorbar medidas contra Agg. Python/JavaScript mantêm equivalência
  no cálculo da escala; exemplo Brasil regenerado com halo branco em Manaus.
- Novas regressões: visibilidade/remoção de ornamentos, simetria da rosa,
  proporção da seta, labels dentro da escala, seleção de estado, minimapa e
  recentering do desktop. Zoom/Home do minimapa HTML foram conferidos no navegador.
- PNG/SVG usam as mesmas métricas verticais dos glifos; regressão compara os
  limites rasterizados com os limites tipográficos. Legenda alinha símbolos
  e textos pelo centro. Escalas editadas mantêm distância correta nos quatro
  cantos; valores inválidos não alteram o componente.
- Grade desligada por padrão, alternância e axisbelow foram comparados ao
  Matplotlib instalado. No navegador foram verificados zoom, grade completa,
  tecla G, foco preto e ausência de erros JavaScript.
- Colorbars: layout da barra e espaço reservado nas quatro posições comparados
  numericamente com o Matplotlib instalado; fixture em colorbar-layout-reference.json.
- Regressões de normalização, atualização de clim/paleta, ticks customizados,
  BoundaryNorm, orientação, visibilidade e remoção de Colorbar.
- Dez hachuras, combinações, densidade por repetição e buracos; campos escalares,
  contornos, iluminação plana e vetores; prioridades de labels entre camadas.
- Preenchimentos fracionários: área de círculos/retângulos em três resoluções;
  concavidade, sobreposição, duplicação de anéis e células com alpha sem frestas.
- Caixas de fundo de textos PNG/SVG comparadas para quatro alinhamentos
  verticais, três horizontais e rotações de 0°, 25° e 90°.
- Wheel instalado em ambiente isolado sem Matplotlib nem Pillow: SVG com fontes
  embutidas e dados geográficos offline funcionou.
- A comparação `gallery/comparison.html` apresenta os mesmos dados desenhados
  por Matplotlib/Agg e Azimlib/Pillow. `gallery/components.png` é inteiramente
  gerado pela Azimlib. Não é screenshot de Matplotlib nem imagem gerada por IA.
- Janelas Tk de ambos os projetos foram inspecionadas; geometria do canvas,
  margens e organização da toolbar seguem a referência. Não há igualdade de
  pixels, de todas as interações nem implementação integral da API Matplotlib.

## Espessura dos traços

Foram medidas 25 combinações: 0,5 / 0,8 / 1 / 1,5 / 2 pontos, nos ângulos
0° / 30° / 45° / 75° / 90°, a 100 DPI. A métrica é a área de tinta dividida
pelo comprimento de uma linha preta de 120 pixels, com extremidades butt.
O Agg foi configurado com snap=False para comparar cobertura contínua.

Antes, uma linha horizontal de 0,8 pt cobria cerca de 1,50 pixel na Azimlib,
contra 1,11 pixel no Matplotlib. O rasterizador agora calcula a interseção
dos polígonos de traço com cada pixel e usa redução por média de área.
Após a correção, o maior desvio de largura média nesta bateria ficou abaixo
de 0,012 pixel. Os resultados estão em `stroke-validation.json`.

Isso valida a espessura integrada de segmentos, não todos os pixels de curvas,
junções, texto ou símbolos. Os testes de regressão também verificam a largura
física esperada sem depender de Matplotlib instalado.

## Limitações restantes

Qt/PDF, animação, raster georreferenciado, grids aninhados/mosaic, normalizadores
completos, picking e shaping complexo de fontes ainda não estão implementados.
O HTML é uma cena exportada, com limitações próprias de navegação e ticks.
Bases densas ainda exigem otimização de índices, recorte e renderização em lote.
Veja `matplotlib-systems.md` e `compatibility.md`.

## Desempenho do PNG

Os buffers/máscaras agora usam tiles locais por primitiva, com clipping e cache
de fontes. Antes/depois no mesmo ambiente, figura 640×480 e seed 123:

| Cena | Antes | Depois |
|---|---:|---:|
| São Paulo + grid + escala, 64 primitivas | 2,45 s | 1,40 s |
| 600 pontos, 627 primitivas | 21,36 s | 0,28 s |

Esses valores são uma medição local de rasterização, sem composição, I/O de
disco ou promessa de desempenho em outras máquinas. Uma execução posterior
registrou 1,11 s e 0,24 s, respectivamente, em raster-benchmark.json.
Reproduza com `python tools/benchmark_raster.py --output resultado.json`.
A aceleração não modifica a geometria do núcleo nem troca o backend.

Após adicionar cobertura fracionária aos preenchimentos, a medição local foi
1,07 s para estado e 0,49 s para 600 pontos (raster-benchmark-quality.json).
Há um custo adicional para qualidade dos marcadores; o ganho sobre 21,36 s
da implementação inicial permanece. Esses dados não incluem composição.

Veja [qualidade visual](image-quality.md) para distinguir desempenho,
resolução, antialiasing e fidelidade ao Matplotlib.

## Composição de legendas e colorbars

Onze regressões verificam colunas, edição de textos/frame, linhas de texto
múltiplas, handles compostos, cor/tamanho de pontos, best, bbox externo,
colorbars compartilhadas, cax, navegação e remoção. Os exemplos de composição
foram exportados e inspecionados em PNG; também possuem SVG e HTML.

`composition-reference.json` foi gerado contra Matplotlib 3.11.2/Agg:
colunas de cinco entradas em grupos de três e duas; best em um cenário
controlado; alocação compartilhada vertical/horizontal (diferença abaixo
de 2×10⁻¹⁶ em frações da figura); cax com seu retângulo preservado.
Isso verifica as regras de composição nesses casos, não toda a aparência
ou comportamento de Legend/Colorbar. A suíte normal não importa Matplotlib.

## Ticks geográficos e colorbars

Treze regressões adicionais verificam posições numéricas, limites, propriedade
por eixo, troca de formatter, textos editáveis, DMS com rollover, zoom,
grade sobre estados preenchidos, cax e a sincronização de ticker/norm.
`ticker-reference.json` contém oito comparações de locator e três de formatter
com Matplotlib 3.11.2, além da regra de clim/norm. Os valores coincidiram
nesses casos, dentro de 10⁻⁹; não é uma validação exaustiva de ticker.

PNG/SVG dos três exemplos foram inspecionados. No navegador, zoom/Home e
rótulos de 2°/DMS foram conferidos, com grade em toda a área e sem erros JS.
Callbacks Python e formatos fora do subconjunto portátil exigem Tk;
veja [ticks](ticks.md). O teste de instalação usa um ambiente sem Matplotlib
e sem Pillow para SVG/HTML, incluindo os controladores de ticks.

## Margens automáticas

Dezesseis regressões verificam títulos multilinha, ticks rotacionados, legendas
externas, visibilidade/exclusão, rótulos com labelpad, padding/rect, resize,
zoom, DPI, colorbars compartilhadas/horizontais/verticais, cax fixo e ajuste
manual. Falhas de espaço e grids mistos restauram posições anteriores.
Uma instrumentação verifica que a medição não reprojeta camadas de dados.

`layout-reference.json` registra a comparação com Matplotlib 3.11.2/Agg:
comportamento de engines, avisos/ajuste manual e limites das decorações
dentro de um canvas 640×480. `gallery/layout-reference.png` compara os mesmos
dados/fontes/estilos, incluindo locator de 2°. As posições e pixels ainda
apresentam diferenças; o solver é independente. A ampliação para um GridSpec
raiz com spans/pesos está descrita abaixo.

Atlas e legenda externa foram exportados em PNG/SVG/HTML e inspecionados.
O atlas no viewer foi verificado com a colorbar completa, sem componentes
adicionados implicitamente. O wheel é validado também sem Matplotlib/Pillow.

A comparação revelou uma inversão do sentido dos ângulos públicos, corrigida
na conversão para coordenadas de tela. Um teste adicional mede a inclinação
real dos pixels de texto em PNG para +25°/-25°, verifica a transformação SVG,
blocos multilinha e edição do rótulo Y. Ângulo positivo é anti-horário, como na
referência Matplotlib. Os rótulos Y/colorbar mantêm o padrão vertical de 90°.

## Rótulos cartográficos

Treze regressões adicionais verificam colisões com annotations, insets e
overview, visibilidade independente de set_in_layout, prioridade entre
camadas/por atributo, filtros por extensão após zoom, uso do trecho visível
quando o centro está fora da vista, direção independente da ordem dos vértices,
rotação explícita, nomes vazios, linhas curtas, buracos e antimeridiano.

Hidrografia em três extensões e demonstração de obstáculos foram exportadas
em PNG/SVG/HTML. Os quatro PNGs foram inspecionados: direção local, legibilidade,
componentes opcionais, foco preto e labels fora de annotations/insets.
Navegabilidade não é inferida. O HTML não refaz a busca dos rótulos no zoom;
recomposição exige Python/Tk. Veja [rótulos](labels.md).

## Ticks menores e grade por grupo/eixo

Quatorze regressões adicionais verificam defaults desligados, ausência de labels
automáticos, estilos separados, edição de TextArtists menores, filtragem de
coincidências, controle X/Y/major/minor/both, zoom, clear/rcParams, ownership,
colorbars horizontais/verticais/log/cax, clim/norm, PNG/SVG/HTML e DPI.
Consultas diretas a Axis antes do primeiro desenho usam o espaço real do mapa.

`minor-ticker-reference.json` foi gerado contra Matplotlib 3.11.2: seis casos
de AutoMinorLocator e quatro colorbars coincidiram nas posições comparadas
até 10⁻⁹. Foram inspecionados três PNGs. No HTML da grade menor, zoom/Home,
alternância G e estilos maiores/menores distintos foram verificados, sem
erros JavaScript. O registro está em `gallery/minor-grid-viewer.png`.

Não cobre toda a API de Tick, offsets científicos ou LogFormatterSciNotation;
veja [ticks menores](minor-ticks.md) e [pendências](pending.md).

## Artists, edição e atualização

Dezesseis regressões adicionais verificam ownership, stale em filhos/pais,
draw_event, falha/reentrância de desenho, callbacks agrupados, referências
fracas, bloqueio/desconexão de sinais, edição inválida de estilos, clear/remove,
identidade de títulos, setp/getp, alpha=None, linhas imutáveis e dados editáveis,
componentes ocultos, insets e colorbars com mappables independentes.

`artist-reference.json` foi gerado diretamente com Matplotlib 3.11.2/Agg.
Os estados de stale antes/depois de editar, limpar um filho, reutilizar título,
remover a linha e restaurar alpha=None coincidiram no protocolo comparado.
Isso não verifica todas as classes/propriedades nem contagens de callbacks.

O exemplo Artists exporta o mesmo mapa antes/depois em PNG/SVG/HTML. Os PNGs
foram inspecionados. A atualização Python é própria do desktop; HTML continua
sendo uma cena independente. Consulte [Artists](artists.md).

O smoke test real de Tk desta etapa não iniciou: o runtime local de Tcl informou
que não encontrou um init.tcl utilizável, inclusive com caminhos explícitos.
Os testes de protocolo/eventos e a suíte passaram, mas o agrupamento real de
redesenhos de Tk desta etapa permanece sem confirmação. O script reproduzível
é `tools/smoke_artist_tk.py`; isso não altera o runtime instalado do usuário.

## Normalização e recomposição de limites

18 testes adicionais cobrem sinais compartilhados, pares de limites atômicos,
substituição/GC de mappables, clip, TwoSlope/LogNorm, dados ausentes e barras
independentes; relim, autoescala por eixo, margens, visibilidade, fit=False,
geometrias/coleções e flags no histórico. A suíte completa passou.

`norm-limits-reference.json` registra oito notificações de mappables e nove
casos de limites/margens/estados obtidos diretamente de Matplotlib 3.11.2/Agg.
O protocolo comparado e os limites numéricos coincidiram (tolerância 1e-9).
Não é uma afirmação de compatibilidade integral com todos os casos de Collections,
sticky_edges, escalas, arrays mascarados ou autoescala do Matplotlib.

O exemplo norm_limits exporta quatro mapas em PNG/SVG/HTML: antes/depois de
uma norm compartilhada e de uma rota com vista automática versus manual.
Os PNGs foram inspecionados. Os dados de cores e rotas são sintéticos.
O wheel isolado verifica estes recursos com SVG, sem Matplotlib/Pillow.
A limitação local de Tcl descrita acima continua aplicável à verificação Tk.

## Coleções geográficas editáveis

13 testes adicionais verificam offsets/sizes/array, cópias e validação, lote
setp, alteração de quantidade, ciclos, pontos vazios/área zero, cores/bordas
na cena e legenda, obstáculos de labels, relim e remoção. Seis estados de
dados/áreas/vista/clim foram comparados com Matplotlib 3.11.2/Agg em
scatter-reference.json. Os limites comparados coincidiram a 1e-9.

Os exemplos scatter-before/after foram exportados em PNG/SVG/HTML e os PNGs
inspecionados. A população de pontos e seus valores são sintéticos. A
verificação do wheel isolado inclui edição de scatter e exportação SVG sem
Matplotlib/Pillow; o smoke desktop continua com a limitação de Tcl acima.

## Orientação com componentes independentes

Sete regressões adicionais verificam coexistência em ambas as ordens,
visibilidade/remoção separadas, setp e validação, desconexão da instância antiga,
ownership/clear, obstáculos de labels/legenda e exclusão dos ornamentos no
overview. O retângulo de decoração HTML inclui ambos, conservando sua política
de ocultação ao navegar uma cena exportada.

orientation-both/arrow-only foram exportados em PNG/SVG/HTML e os PNGs
inspecionados. A geometria visual da rosa foi preservada. O wheel isolado
verifica os dois handles, edição, visibilidade e SVG sem Matplotlib/Pillow.
As orientações são extensões cartográficas próprias, não objetos copiados de Matplotlib.

## Edição de campos escalares e vetoriais

Catorze testes novos cobrem origin/forma/extent, arrays planos e matrizes de
células, setp agrupado, dados ausentes, normalização prospectiva, UVC/broadcast,
offsets/scale, entradas inválidas sem mutação parcial, relim, exportação e
desconexão de handles removidos. A suíte completa passou.

field-edits-reference.json registra oito estados de imagem, dois de mesh e
quatro de vetores efetivos obtidos com Matplotlib 3.11.2/Agg. Valores, extent,
limites de cores, coordenadas de células e vistas manuais comparadas coincidiram.
Isso não iguala formatos internos: get_array permanece plano na Azimlib,
vetores escalares são expandidos e máscaras/RGB ainda não têm suporte próprio.

fields-before/after mostram os mesmos handles editados e a norm compartilhada,
exportados em PNG/SVG/HTML. Os PNGs foram inspecionados; os campos são sintéticos.
O wheel isolado verifica imagem/mesh/UVC, colorbars e SVG sem Matplotlib/Pillow.
A verificação desktop continua com a limitação de Tcl já descrita.

## GridSpec, spans e proporções

Doze regressões novas verificam seleções, índices negativos, pesos, margens,
gaps, herança/edição de parâmetros, propriedade da Figure, validação antes de
alterar posições, bordas do canvas e pesos muito pequenos. Elas cobrem também
tight/constrained com spans, títulos/ticks e colorbar compartilhada, resize,
DPI, cax explícito, grids não utilizados, e rollback se a Figure não comportar
as decorações. A suíte anterior de grids regulares continua passando.

gridspec-reference.json registra 24 seleções, seis estados de edição e três
seleções numéricas de Matplotlib 3.11.2/Agg. A alocação manual coincide nos casos
comparados, com tolerância de 12 casas decimais em frações de Figure. Isso não
declara igualdade do viewport final, aspecto, solver automático ou pixels.
O solver suporta um GridSpec raiz; grids aninhados/múltiplos são pendências.

gridspec-atlas foi exportado em PNG/SVG/HTML e o PNG inspecionado: Brasil em um
span de duas linhas, MG/SP à direita, barra compartilhada e ornamentos opt-in.
Valores são sintéticos. O wheel isolado verifica spans/proporções, recálculo e
exportação SVG sem Matplotlib/Pillow.

## Rótulos adaptativos da barra de escala

Seis regressões verificam ausência de colisões e contenção dos rótulos no frame,
redução de três graduações para duas/uma, preservação de fonte e distância,
os quatro cantos, unidades m/km/mi, resize, zoom, fontsize editável, visibilidade,
DPI e exportação SVG/HTML. Os testes de distância usam tolerância relativa de
1e-9; o padding final participa da medição no ponto em que a barra é desenhada.

scale-labels foi exportado em PNG/SVG/HTML e o PNG inspecionado com três larguras,
100 km e a mesma fonte em todos os mapas. O atlas também foi regenerado com os
comprimentos originais de 100/200 km, agora sem os números intermediários que
colidiam. O wheel isolado verifica os três planos de rótulos em SVG sem Pillow.
A escala continua uma extensão própria, não um componente nativo do Matplotlib.

O modo compacto também encolhe a caixa, removendo a linha inferior ausente.
A regressão verifica altura, folga abaixo da barra e ancoragem nos quatro cantos;
os testes de distância se aplicam à nova posição final. scale-labels foi regenerado
e inspecionado com o frame menor.

## Desempenho de mapas completos e atalhos raster

benchmark_maps.py mede setup/primeira composição, composição repetida, SVG, PNG,
zoom + recomposição e pico Python da composição em uma passagem separada.
São Paulo, Brasil, atlas com spans e 1.500 pontos foram medidos em 100 DPI;
São Paulo também em 200 DPI. Nenhum desses números mede latência real de GUI.

compare_raster_versions.py usa snapshots confiáveis do renderer anterior sobre
a mesma Scene, alternando a ordem em quatro pares por mapa a 100 DPI e dois
pares do estado a 200 DPI. Todos os PNGs foram idênticos por SHA-256. Os ganhos
locais foram modestos; diferenças pequenas e a amostra curta não estabelecem
aceleração geral ou significância estatística. Veja [relatório](performance.md).

Três regressões novas verificam áreas analíticas de fragmentos, clipping nas
bordas, cobertura em múltiplas linhas, união sem sobrepintura e os 256 níveis
de alpha ao reutilizar/evictar tabelas. A suíte anterior continua passando,
incluindo traços finos por ângulo, preenchimentos, caps, opacidade e clipping.
O pico tracemalloc exclui buffers nativos, dados carregados antes e memória RSS.
Persistem os gargalos de cobertura/clipping, índice espacial, cache de vértices,
bases densas reais e renderização incremental; o critério 0.2 não está fechado.

## Limites reutilizados e descarte conservador por viewport

Nove regressões novas verificam limites exatos das seis projeções internas,
mudança de parâmetros/resize, cache limitado/evicção, subclasses customizadas,
bounds imutáveis/serialização, cruzamentos, polígonos envolventes e buracos,
hachuras, traços grossos, símbolos, antimeridiano/longitude não normalizada,
geometrias compostas, clipping polar Mercator, callbacks/cores por feature,
set_data, histórico, insets, minimapa e exportação com override de DPI menor.
PNG completo/otimizado é comparado diretamente, incluindo 35/100/200 DPI.

compare_composition.py alterna quatro passagens dos três modos sobre São Paulo,
Brasil, atlas e 2.501 polígonos sintéticos. Os PNGs foram idênticos por SHA-256;
as prévias de São Paulo/atlas foram inspecionadas. Veja [desempenho](performance.md).
O HTML conserva as geometrias invisíveis para navegação. Não há ainda índice
espacial ou cache de todas as coordenadas projetadas. Esta medição exclui
latência de GUI; a limitação de Tcl/desktop neste ambiente permanece.

Após esta entrega: **291 testes e 1.721 subtests passaram**. Wheel/sdist foram
construídos; o wheel foi instalado offline, sem dependências, em ambiente sem
Matplotlib e Pillow. Bounds/viewport/culling, SVG/HTML, edição dos campos,
componentes, GridSpec e escala compacta foram verificados nessa instalação.

## Índice espacial e overscan de hachuras

Nove testes novos incluem 120 consultas aleatórias confrontadas com varredura
independente, caixas que tocam/envolvem a consulta, caixas duplicadas/sem área,
entrada editada após construção, validação e imutabilidade. Na integração,
primitivas/metadados e PNG são comparados à composição com descarte linear,
com redução verificada do número de geometrias processadas. Cobrem pan/zoom/DPI,
cores e ordem originais, callbacks completos, overrides editados diretamente,
projeção/evicção, substituição de dados, geometrias especiais, insets e minimapa.
HTML é verificado pelo caminho de cena completa.

Uma regressão compara também à imagem sem descarte quando uma hachura grossa
de um polígono fora da vista alcança o mapa. A folga considera hatch_linewidth,
além da borda, e reage à edição desse valor.

benchmark_spatial.py alterna seis pares em cinco mapas/cargas e separa preparação
do índice, composição/zoom reutilizados e alocações Python em outra passagem.
Todas as cenas e PNGs ficaram idênticos; as prévias Brasil/carga de 20.000 polígonos
foram inspecionadas. Há ganho nas bases sintéticas e custo inicial mensurável;
isso não valida municípios reais, latência GUI ou memória nativa.

Após esta entrega: **300 testes e 1.854 subtests passaram**. O wheel isolado
verifica consulta/ordem do BVH, composição indexada, SVG/HTML e os recursos
anteriores, sem Matplotlib/Pillow. A limitação de Tcl permanece para smoke GUI.

## Largura adaptativa da caixa de escala

Duas regressões adicionais medem a folga horizontal exata de meia fonte, em
três larguras, quatro cantos e unidades/comprimentos distintos, incluindo uma
barra quase sem largura sob a caption. O modo compacto mede só o texto/barra
presentes; os modos normais preservam margens independentes das extremidades.
Também verificam a distância final em equiretangular, Mercator, Albers e Lambert,
com tolerância relativa de 1e-9. As regressões anteriores de labels/altura/edição
e unidade permanecem passando.

Após esse ajuste: **302 testes e 1.918 subtests passaram**. Os exemplos de escala,
atlas e estado foram regenerados em PNG/SVG/HTML com a caixa ajustada ao conteúdo.

## Escala centralizada e preparação espacial compacta

A escala agora usa margens simétricas para centralizar a barra, com meia fonte
de folga além do conteúdo mais largo. Os 48 casos de largura/unidade/canto
verificam centro e padding; modos compactos e distância final permanecem cobertos.

Uma regressão adicional compara caixas finas, sobrepostas e de coordenadas
extremas, float64 adjacentes e chaves inteiras grandes com varredura independente,
em seis tamanhos de folha, inclusive uma capacidade inteira arbitrariamente
grande. A consulta inclui bordas e caixas sem área, sem quantização.
A suíte completa passou: **303 testes e 1.954 subtests**.

compare_spatial_builders.py compara o BVH anterior da própria Azimlib à preparação
STR compacta: bounds igualmente aquecidos, seis pares alternados de índices novos,
consultas focadas/completas, alocações Python em outra passagem e comparação
de Scene/PNG. Veja [desempenho](performance.md). O índice não fecha o critério
0.2: memória nativa, bases municipais reais e latência GUI continuam pendentes.

Galeria de escala/atlas/estado regenerada em PNG/SVG/HTML, com escala e São Paulo
inspecionados visualmente. Wheel/sdist construídos; instalação offline do wheel
sem dependências verificou o índice, SVG/HTML, componentes e escala centralizada,
em ambiente sem Matplotlib/Pillow. Smoke nativo permanece limitado pelo Tcl.

## Reutilização de paths projetados

Nove regressões adicionais confrontam Scene/SVG/PNG sem cache e com cache
inicial/aquecido, incluindo 42 pares de projeção/forma de geometria. Cobrem
multipartes, buracos, vazios, elevação, antimeridiano, longitude não normalizada,
clipping polar Mercator e horizonte ortográfico; estilos, curvas/arrows/marcadores,
hachuras e callbacks continuam sendo atualizados após a preparação.

São verificados `set_data`, parâmetros de projeção, nova escala/posição do viewport,
DPI, culling, insets/minimapa e HTML completo. Uma regressão bloqueia `forward`
durante um desenho aquecido para assegurar que seus vértices não são reprojetados.
Outras verificam orçamento/LRU, fontes liberadas via weakref, Scene editada sem
contaminar o cache, falhas não retidas e subclasses customizadas fora do cache.

A suíte completa passou: **312 testes e 2.004 subtests**. A implementação mantém
independência de bibliotecas geoespaciais/Matplotlib. Comparação alternada com
o compositor anterior próprio e [limites de medição](performance.md).

Os cinco casos do benchmark (São Paulo, Brasil, atlas, malha sintética e globo)
preservaram primitivas/metadados e PNG por SHA-256. Prévias de atlas/globo
inspecionadas. Wheel/sdist construídos, com instalação offline sem dependências:
reutilização de vértices, limite de armazenamento, mudança de viewport e
igualdade de Scene passaram em ambiente sem Matplotlib/Pillow. A checagem cobre
também os componentes e recursos anteriores. A limitação de Tcl/GUI permanece.

## Lotes de mappables, dados e cores

Onze regressões novas confrontam 20 estados finais de Matplotlib 3.11.2/Agg
registrados pelo tool de desenvolvimento inspect_mappable_batches.py: imagem,
mesh, pontos e vetores, lotes de array/cmap/clim/alpha/visibilidade, troca de
normalização, atribuição cmap e paleta padrão. A comparação verifica também
referência compartilhada da norm e preservação/reset do locator da colorbar.

Regressões próprias incluem camada coroplética, dados/geografia com cores no
mesmo lote, estado final nos callbacks de Artist/mappable, norm compartilhada,
desconexão da antiga, pré-validação sem mutação de norm externa, inválidos
preservando dados/estilos/visibilidade/ticks/stale, e 24 ordens de argumentos.
Missing values, LogNorm, TwoSlopeNorm, BoundaryNorm, norm=None, clim parcial,
getp e PNG/SVG/HTML são cobertos. Setters isolados de ScalarMappable também
validam a normalização prospectiva antes de alterar array/conexões.

**323 testes e 2.075 subtests passaram.** Scene/PNG de lote e setters dedicados
são comparados; a garantia de validação/coalescência é da Azimlib, não uma
promessa de contagem de sinais/transações igual ao Matplotlib.
Veja [contrato e referência](mappable-batches.md). A entrega seguinte amplia
a edição de contornos; reclassificação de legendas continua pendente.

O exemplo mappable_batches.py exportou antes/depois em PNG/SVG/HTML, com os
PNGs inspecionados. Wheel/sdist construídos e wheel reinstalado offline sem
dependências em ambiente sem Matplotlib/Pillow. Edição agrupada de imagem,
norm/clim/paleta, sinais finais, política de ticks da colorbar e preservação
após lote inválido passaram nessa instalação, junto dos recursos anteriores.

## Lote de linhas, marcadores, contornos e rótulos

Cinco avanços relacionados foram implementados e verificados juntos, com
16 regressões novas e 95 subtests adicionais. Quatro estados de linha, três
de contorno e um protocolo de rótulos foram registrados diretamente de
Matplotlib 3.11.2/Agg pelo tool inspect_lines_contours.py. Não é uma promessa
de compatibilidade integral nem de igualdade de pixels.

Verificações incluem dados/estilos/visibilidade de linhas em lote e 24 ordens
de propriedades; getters/setters de marcadores/caps/junções, marcador auto/None,
texto/annotation em lote, fontes imutáveis, vista manual e falhas sem edição
parcial. Contornos ciclam widths/styles/cores por nível, inclusive múltiplos
caminhos; clabel tem seleção de níveis, fmt e handles individuais, visibilidade
separada, atualização de cores e remoção associada. Fontes inválidas/edições
rejeitadas preservam callbacks/stale/dados/componentes. getp, vazio, clear e
detachment também são cobertos.

A integração compara Scene/PNG de lote com setters dedicados, além de SVG/HTML.
Culling de 160 caminhos em Mercator/equiretangular preserva PNG com larguras
distintas por nível antes/depois da edição. A suíte completa passou:
**339 testes e 2.170 subtests**. O teste de exportação atômica agora exige que
marcadores inválidos sejam rejeitados no setter antes do desenho.

O exemplo lines_contours.py gerou mapas antes/depois em PNG/SVG/HTML;
ambos os PNGs foram inspecionados. As diferenças atuais estão no
[contrato](lines-contours.md); o lote seguinte corrige os valores por caminho
e acrescenta inline cutting e colorbar de isolinhas.
O critério de Artists da 0.2.0 avançou; nenhum dos cinco critérios foi declarado
fechado. O smoke Tk continua limitado pelo init.tcl indisponível neste ambiente.

Wheel/sdist construídos; wheel reinstalado com --no-index/--no-deps em ambiente
sem Matplotlib/Pillow. Dados/markers/caps de linha em lote, ContourSet com
widths/cmap/clim, rótulos individuais, SVG/HTML e remoção associada passaram,
junto das verificações offline dos recursos anteriores. Publicação no PyPI
não foi realizada e a versão permanece 0.1.0 alpha.

## Valores por nível, barras de isolinhas e cortes inline

Três avanços integrados, com 11 regressões e 45 subtests adicionais.
inspect_contour_bars.py registra 12 casos de Matplotlib 3.11.2/Agg:
cores mapeadas/explícitas/LogNorm, duas orientações e dois spacings;
norm, array, clim, boundaries, values, ticks, posições e larguras.
Também registra NoNorm e defaults inline=True/inline_spacing=5.
As posições numéricas e os contratos registrados são confrontados nos testes;
o pacote não importa nem usa o backend da referência.

Testes cobrem níveis vazios e oito caminhos desconectados, edição de valores,
paleta de uma cor/under/over/bad, cores manuais separadas da paleta da barra,
tickers retidos/substituídos, quatro posições de barra e cax.
Cortes próprios são verificados em segmentos rotacionados/invertidos, união
de cortes e ocultação total; edição de fonte/folga altera a abertura.
Rótulos ocultos/removidos/transparentes/não posicionados não cortam linhas;
outros contornos não são afetados. Fontes/allsegs continuam imutáveis,
cache projetado é reutilizado e PNG completo/culling é idêntico em duas
projeções e três DPI. SVG/HTML e pan/zoom também são exercitados.

A suíte completa passou: **350 testes, 2.215 subtests**, em 71,887 s neste
ambiente. contour_refinement.py gerou PNG/SVG/HTML antes/depois com mapas
Mercator e barras uniform/proportional. Os PNGs e a comparação lado a lado
de compare_contours.py foram inspecionados. Não há promessa de igualdade
de pixels: posição de rótulos, algoritmo de recorte e layout seguem o núcleo
próprio. set_array permite edição de cor explícita, diferente do reset da
referência. Esses limites estão documentados.

Wheel/sdist foram construídos e o wheel reinstalado com --no-index/--no-deps
em ambiente separado sem Matplotlib/Pillow/GIS. NoNorm/valores por nível,
colorbar de linhas, cortes reversíveis e SVG/HTML passaram junto dos smokes
anteriores. PNG foi verificado pela suíte e pela galeria no ambiente com
Pillow; o extra azimlib[png] continua necessário para essa exportação.
0.2.0 não foi fechada, nem houve publicação no PyPI.

## Figuras, seleção de eixos e mosaicos planos

Três avanços relacionados e 13 regressões com 38 subtests adicionais.
inspect_figure_state.py registra diretamente de Matplotlib 3.11.2/Agg sete
estados de números/labels/ativação/fechamento, cinco de seleção/remoção de
eixos e oito layouts de mosaicos, incluindo vazios, pesos e nomes não string.
Os testes confrontam números, labels, ordem de eixos, seleção, spans e
posições nominais em frações de Figure.

Integrações cobrem sca entre figuras e destino de plot/title/savefig, reuso de
subplot por spec/span/projeção, limpeza com desconexão de colorbars/Artists,
renomeação/título HTML, seleção após remoção de cax e exclusão de insets filhos.
Validação de mosaicos rejeita retângulos incompletos, pesos/projeções/opções
inválidos antes de alterar eixos/grid/stale. Dois engines compõem spans com
títulos/ticks/colorbar compartilhada e ornamentos opcionais dentro do canvas.
Uma janela simulada verifica o encaminhamento do título; não substitui o
smoke Tk ainda limitado neste ambiente pelo init.tcl indisponível.

A suíte completa passou: **363 testes, 2.253 subtests**, em 87,482 s neste
ambiente. figure_state.py gera atlas Brasil/SP/AM antes/depois em PNG/SVG/HTML;
os PNGs foram inspecionados. A legenda do exemplo usa explicitamente só o
handle da rota, evitando classes do coroplético junto da escala. Os valores
regionais são sintéticos. compare_mosaic.py gera uma referência Agg com a
mesma base geográfica, fonte e DPI; alocação nominal é comparada numericamente,
sem promessa de igualdade de pixels ou de todo o layout automático.

Naquele lote, mosaicos/grids aninhados e eixos compartilhados ainda estavam
pendentes; o lote seguinte acrescenta hierarquias. A versão continua 0.1.0 alpha.

Wheel/sdist construídos e wheel reinstalado com --no-index/--no-deps em
ambiente sem Matplotlib/Pillow/GIS. Ciclo de figuras numeradas/nomeadas,
seleção do eixo/destino de desenho, reuso de subplot, mosaico com solver,
limpeza e exportação SVG/HTML passaram junto dos smokes anteriores.
PNG foi conferido na suíte e nos exemplos com o extra Pillow disponível.
Publicação no PyPI não foi realizada; nenhum critério completo da 0.2 foi fechado.

## Grids filhos, mosaicos e composição hierárquica

Três avanços integrados e 12 regressões novas, com 33 subtests adicionais.
inspect_nested_layout.py registra 10 seleções/posições e parâmetros nominais,
quatro estados de atualização e três mosaicos de Matplotlib 3.11.2/Agg.
Os testes confrontam pesos/gaps/herança de parâmetros, alocação/topmost spec,
ordem dos nomes e propagação manual de alterações do pai aos filhos.
Nenhum módulo cartográfico importa Matplotlib.

As integrações verificam binding de hierarquias sem Figure, rejeição de uso
em outra Figure e isolamento de seleções numéricas em relação a grids filhos.
Mosaicos incompletos, nomes globais repetidos, projeções/gaps/pesos inválidos
e profundidade cíclica são rejeitados antes de anexar eixos/grid ou marcar stale.
Há teste de projeção individual em nome de nível interno e cópia dos inputs.

Os dois engines próprios medem uma hierarquia com spans, títulos em duas
linhas, ticks rotacionados, componentes opcionais e colorbars compartilhadas.
Bounds compostos ficam dentro do canvas e separados por grupo. Edições de
texto/pesos, resize, ocultação/remoção e eixos fora de layout são exercitados.
Falhas de tamanho, título excessivo, grids raiz distintos e erro inesperado
de medição restauram todas as posições/parâmetros anteriores. Um único eixo
ativo em uma seleção filha conserva sua alocação no pai. Dois DPI preservam
PNG entre composição completa/culling; SVG/HTML e zoom são verificados.

A suíte completa passou: **375 testes, 2.286 subtests**, em 96,305 s neste
ambiente. nested_atlas.py gerou PNG/SVG/HTML antes/depois da edição de pesos
e títulos, com colorbar do grupo regional. Ambos os PNGs e a comparação de
compare_nested_layout.py foram inspecionados. A referência numérica compara
alocação manual; o solver hierárquico é próprio e não promete reproduzir
as posições automáticas de Matplotlib. Naquele lote, SubFigure/eixos compartilhados e
múltiplos grids raiz em layout automático continuam pendentes.

Wheel/sdist foram construídos; o wheel foi reinstalado com --no-index/--no-deps
em ambiente sem Matplotlib/Pillow/GIS. Grids filhos, herança/atualização de
ancestrais, mosaicos aninhados, solver próprio e colorbar do grupo passaram
em SVG/HTML junto dos smokes anteriores. PNG foi verificado pela suíte e pela
galeria com Pillow disponível. Publicação no PyPI não foi feita e 0.2.0 não
foi fechada nesta etapa.

## Longitude/latitude compartilhadas e rótulos externos

Dezoito regressões adicionais verificam grupos próprios de limites/tickers,
união dos dados para autoescala, margens/flags locais, emit=False/auto=None,
callbacks de limites, construção manual e reuso de pyplot.subplot. O oracle
shared-axes-reference.json foi registrado de Matplotlib 3.11.2/Agg: 36
combinações de sharex/sharey, visibilidade externa, limites de dados, flags
e rótulos em um mosaico aninhado. Defaults geográficos vazios permanecem
próprios da Azimlib; não se comparam com os limites cartesianos 0..1.

As regressões também cobrem tickers maiores/menores compartilhados, estilo
de rótulos local, label_outer/remove_inner_ticks, remoção do eixo principal,
clear preservando vínculo, figuras distintas e clone do overview isolado.
Tamanhos diferentes e duas composições consecutivas conservam as posições
automáticas dos ticks, sem depender da ordem do desenho ou de caches anteriores.
O modelo de Navigation restaura vistas e flags individuais no grupo.

shared_axes.py produz quatro camadas (político, rios, coroplético, rotas),
com uma vista editada a partir de um painel, rótulos externos e colorbar opt-in.
PNG/SVG antes/depois foram gerados; os PNGs e a comparação lado a lado de
compare_shared_axes.py foram inspecionados. A composição/traços/textos se
aproximam de Agg, sem promessa de igualdade de pixels ou de todo o layout.

A suíte completa passou: **393 testes, 2.326 subtests**, em 100,122 s neste
ambiente. Os 18 testes específicos também passaram separadamente. Não há
validação Tk real neste lote, pois init.tcl continua ausente. A sincronização
interativa foi verificada no modelo Python usado por Tk; o HTML portátil
naquele momento navegava painéis independentemente. O exemplo exporta PNG/SVG.

## Navegação portátil vinculada e exportação corrente

Onze regressões adicionais executam o JavaScript realmente distribuído usando
metadados produzidos pelo núcleo Python. Dois testes verificam metadados/DPI e
separação entre HTML interativo e SVG estático. Nove casos Node cobrem oito
estados registrados de Matplotlib 3.11.2/Agg, 36 combinações de grupos,
aspecto, zoom por dimensão, âncora, pan, cancelamento, ramificação do histórico,
projeções cilíndricas distintas, domínio comum, limites extremos, índices de
eixos ocultos e mosaicos aninhados. Node é opcional no desenvolvimento.

A suíte completa passou: **404 testes, 2.326 subtests**, em 90,247 s neste
ambiente. A correção inclui MapAxes isolados sem Figure; cinco regressões
existentes desse caminho também foram executadas separadamente.

portable_navigation.py gerou PNG/SVG/HTML para atlas vinculado e grupos por
linha/coluna. A verificação headless em Microsoft Edge/Chromium, num contexto
Playwright novo, passou em 12 cenários: retângulo, pan, histórico da Figure,
Home, cursor, pointercancel, roda, overview, salvar SVG/PNG, grupos por coluna
e restrição x. Nenhum erro de página ocorreu. Os screenshots inicial, ampliado
e de grupos foram inspecionados. O PNG baixado conserva fundo branco opaco;
970 pixels internos adjacentes da colorbar coincidem exatamente com sua paleta,
sem frestas. A borda externa foi excluída dessa regressão específica.

O modelo preserva aspecto e sincroniza grupos cilíndricos; não recompõe toda a
cena Python. Naquele lote, ornamentos dependentes da vista continuavam ocultos após navegar,
até Home. Outras projeções vinculadas e GUI Tk real continuam pendentes.
Veja [contratos e ferramentas reproduzíveis](portable-navigation.md).

Wheel/sdist foram construídos. O wheel foi reinstalado com --no-index/--no-deps
em ambiente sem Matplotlib, Pillow ou bibliotecas GIS; o smoke cumulativo passou,
incluindo assets JavaScript próprios, grupos/caixas/tickers serializados e os
recursos anteriores em SVG/HTML. PNG foi validado no ambiente de desenvolvimento
com Pillow e no browser. As ferramentas JavaScript de QA são incluídas no sdist;
não são dependências de execução. A versão continua 0.1.0 alpha, sem publicação
no PyPI e sem declarar concluídos os cinco critérios da 0.2.0.

## Escala e orientação durante a navegação portátil

O escopo foi registrado: roteiro urbano, 3D e demais expansões fora do corte
ficam após a 0.2.0. A consolidação 2D continua sendo o trabalho atual.

Duas regressões novas verificam a ausência de componentes por padrão, exportação
somente de Artists visíveis, independência entre norte/rosa, remoção, índices,
metadados em dois DPI e separação entre SVG estático e HTML. Executam também
components.js realmente distribuído contra 147 composições próprias Python:
duas projeções, três unidades, quatro cantos, três larguras e dois DPI, além de
comprimentos explícitos com/sem frame e erro quando não cabe. Coordenadas,
primitivas, estilos, métricas/baselines, graduações e unidades são comparados;
oito deslocamentos de orientação e 11 formatos numéricos também são cobertos.
Não se usa Matplotlib como oracle desses componentes cartográficos ausentes
do seu núcleo.

A suíte completa passou: **406 testes, 2.326 subtests**, em 89,906 s neste
ambiente. A comparação específica passou separadamente. A verificação headless
foi ampliada para **20 cenários**, sem erros de página: distância recomposta,
tamanho fixo de orientação, Home/histórico, pan, SVG/PNG da vista corrente,
aviso para comprimento explícito que não cabe e ausência opcional, junto das
12 verificações anteriores. O PNG da vista corrente tem 1000×500 pixels e fundo
branco opaco; foi inspecionado, assim como o screenshot após zoom. A regressão
de 970 pixels adjacentes da colorbar continua passando sem frestas.

Em Mercator/equiretangular contínuas, a escala recompõe medida e layout com
métricas próprias; norte/rosa são reancorados com dimensões físicas preservadas.
Projeções descontínuas/não cilíndricas mantêm a ocultação após navegar até Home.
Solver geral, reposicionamento de legendas/rótulos e GUI Tk real continuam
pendentes; não há promessa de recomposição Python completa no navegador.

Wheel/sdist foram reconstruídos e o wheel foi reinstalado offline sem
dependências. O smoke cumulativo passou em ambiente sem Matplotlib/Pillow/GIS,
incluindo os novos assets, métricas, visibilidade e metadados de escala/norte/rosa.
PNG foi validado separadamente no desenvolvimento e no browser. O ZIP-fonte
inclui os exemplos, screenshots e ferramentas de QA. Nenhuma versão foi
publicada ou alterada para 0.2.0 nesta etapa.

## Mapas completos, clipping de cobertura e memória de processo

Três regressões novas comparam a cobertura com um snapshot próprio anterior:
628 casos parametrizados de máscaras frescas/acumuladas, polígonos fracionários,
côncavos, degenerados, auto-intersectantes e fora do canvas, diferentes valores
de cobertura e elipses. Também verificam menos chamadas de clipping quando o
semiplano já contém os vértices e PNG byte a byte igual com caps/junções,
tracejado, transparência e clipping. Não há quantização, mudança de geometria,
antialiasing ou DPI nessa otimização.

A suíte completa passou: **409 testes, 2.954 subtests**, em 91,445 s neste
ambiente. Na comparação alternada serial de mapas completos, PNGs ficaram
idênticos por SHA-256 em São Paulo/Brasil/atlas a 100 DPI (quatro pares) e
São Paulo/atlas a 200 DPI (dois pares). Reduções medianas locais entre 5,2% e
11,2%; amostras pequenas, sem significância estatística/garantia geral ou GUI.

Nove pares da mesma Scene cartográfica foram exportados contra Agg:
São Paulo/Brasil/atlas em 100/150/200 DPI, com PNG próprio, Agg, comparação,
diferença e SVG. São diagnósticos de rasterização, não comparação independente
de Axes/layout/geografia do Matplotlib. Os exemplos São Paulo/Brasil em 100 DPI
e atlas em 200 DPI foram inspecionados. Há diferenças de hinting/antialiasing
e posição subpixel; não há igualdade de pixels declarada nem encerramento do
critério visual. O adaptador de desenvolvimento conserva clips/alpha/buracos
simples e tem limites explícitos para halos e caminhos complexos.

A memória foi medida em seis workers novos, sem Matplotlib/GIS, para três
mapas em 100/200 DPI. Windows GetProcessMemoryInfo inclui runtime, dados,
alocações Python e buffers nativos: working set, pico desde o início do processo
e compromisso privado são conceitos distintos. Pico observado do atlas em
200 DPI: 403,46 MiB. Não se subtrai baseline nem se chama esse valor de pico
isolado de uma etapa. O fallback Unix não foi executado aqui.

Veja [comparações e limites](complete-map-quality.md) e
[amostras de desempenho/memória](performance.md). Buffers temporários, mais
estilos/DPI, GUI nativa e CI nas plataformas suportadas continuam pendentes.

## Buffers PNG e comparação de memória antes/depois

Cinco regressões adicionais confrontam o renderer com seu snapshot próprio
anterior. Foram 207 novos casos parametrizados de fundos transparentes/coloridos,
fill/stroke/RGBA/alpha global, buracos, tracejados, clipping fracionário e textos
com fundo/halo/rotação em três resoluções; os PNGs ficaram byte a byte iguais,
inclusive com reutilização da Scene. Também verificam menor volume de buffers
RGBA alocados, liberação de tiles/máscaras próprios antes do encoding e
propriedade do stream do chamador após sucesso/falha de escrita. Intermediários
de rotação pertencentes ao Pillow não são tratados como buffers próprios.

A suíte completa passou: **414 testes, 3.161 subtests**, em 112,179 s neste
ambiente. Comparações seriais de tempo conservaram os hashes PNG dos mapas
completos: quatro pares em 100 DPI e dois em 200 DPI. O tempo variou pouco
nos dois sentidos, sem aceleração geral declarada. A amostra do atlas que
coincidiu com testes foi descartada e repetida serialmente.

A memória foi comparada separadamente, em 24 workers novos e ordem alternada,
dois pares por mapa/DPI, com 96 registros de etapas. Ambos os modos carregam
os mesmos módulos antes de selecionar o renderer. Scenes/dimensões/quantidade
de itens e hashes PNG coincidiram; fontes dos renderers e contadores positivos
foram auditados. Nenhum worker importou Matplotlib/GIS. São Paulo a 200 DPI
teve pico mediano de 200,22 → 192,12 MiB (4,0%); atlas a 200 DPI, 403,32 →
401,34 MiB (0,5%). Pico é do processo inteiro desde o início, não de uma etapa
isolada nem só de buffers nativos. Poucas amostras e variação do OS limitam a
interpretação; GUI e fallback Unix continuam sem execução real.

Veja [resultados, dados brutos e reprodução](performance.md#reutilização-e-liberação-de-buffers-png).
Esta entrega não altera o corte da 0.2.0 nem antecipa urbano/3D.

## Composição RGBA e redução BOX em faixas

Oito regressões adicionais e 97 novos subtests comparam o caminho em faixas
com a operação integral: RGBA aleatório/alpha extremo/RGB sob alpha zero,
linhas alternadas e divisões entre faixas, offsets e última faixa parcial,
orçamento menor que uma linha, inputs emprestados/erros/liberação de temporários,
caminho pequeno sem crops próprios e PNGs completos em quatro resoluções com
fontes/halo/fundo/rotação/buracos/tracejado/clipping. Supersampling 3x, filtro
BOX, modo RGBA, dimensões e bytes PNG permanecem iguais ao renderer anterior.

A suíte final passou: **422 testes, 3.258 subtests**, em 118,355 s neste
ambiente. Comparações seriais de tempo usaram quatro pares em 100 DPI e dois
em 200 DPI; PNGs completos de São Paulo/Brasil/atlas mantiveram SHA-256 igual.
O tempo variou nos dois sentidos, incluindo regressão local de 5,2% no caso
São Paulo/200 DPI. Não há aceleração geral declarada.

A estratégia usa faixas para fontes acima de 16 MiB; fontes pequenas conservam
o caminho anterior. O orçamento de 4 MiB por crop próprio pode ser ultrapassado
pelo mínimo de uma linha inteira (três linhas fonte no BOX), e não é um limite
do renderer/processo inteiro. Todos os buffers do canvas não foram eliminados.

Na comparação final de 24 workers novos/96 registros, hashes/metadados dos PNGs
coincidiram e contadores/fontes do código foram auditados. São Paulo/200 DPI:
192,01 → 156,17 MiB de pico mediano (18,7%); atlas/200 DPI: 401,10 → 288,08
MiB (28,2%). O pico é do processo inteiro desde seu início, não só da operação
nativa. Dois pares por caso/DPI não estabelecem uma garantia geral. Cada worker
carrega ambos os renderers antes da seleção; nenhum importa Matplotlib/GIS.

Duas passagens diagnósticas separadas registram callbacks em operações grandes
de resize/composição (36 eventos antes, 198 depois). Não entram nos benchmarks
nem observam todas as alocações transitórias nativas. GUI/fallback Unix/CI
nas plataformas suportadas continuam sem execução real.

Veja [dados, limites e reprodução](performance.md#canvas-composição-e-redução-box-em-faixas).


## Estilos/recortes e aritmética dos traços

Quatro testes adicionais/3.041 subtests verificam floats byte a byte, vértices,
máscaras novas/acumuladas e PNGs completos contra a cobertura própria anterior.
A suíte completa passou: **426 testes, 6.299 subtests**, em 88,949 s neste
ambiente. A duração da suíte não é benchmark comparativo de performance.

Cinco medições de mapas completos, alternadas e seriais, preservaram hashes PNG
com redução local mediana de tempo de 6,6% a 13,3%. Não se mediu novo pico de
memória ou latência GUI. Veja [método e dados](performance.md#aritmética-da-cobertura-dos-traços).

Nove pares de estilos/recortes/hachuras contra Agg foram gerados em 100/150/200
DPI; dimensões, hashes PNG, fingerprints de código e XML/dimensões de nove SVGs
conferidos. Três painéis foram inspecionados visualmente. A comparação reutiliza
a Scene da Azimlib e não testa o gerador de hachuras/layout/viewer do Matplotlib;
diferenças de suavização/fontes permanecem. Veja [escopo e resultados](style-quality.md).

Wheel/sdist foram gerados e o wheel instalado novamente em ambiente isolado:
SVG/HTML, fontes/dados/componentes e os smokes acumulados passaram sem Pillow,
Matplotlib ou bibliotecas GIS. Em instalação separada com Pillow, o PNG de
canvas 3x acima de 16 MiB ficou byte a byte igual ao renderer próprio anterior;
fontes embarcadas e propriedade do stream também passaram. Código do wheel,
metadata de dependências e inclusão das novas fontes/testes/docs no sdist
foram auditados; o ZIP fonte inclui os nove pares e seus SVGs.
GUI real em Tk funcional e CI nas plataformas suportadas continuam pendentes;
esta entrega não fecha a 0.2.0 nem antecipa urbano/3D.


## Rótulos globais e edição de textos da Figure

Doze regressões novas (50 subtests) verificam rótulos globais/posição/defaults,
reutilização, setters agrupados, invalidação/callbacks, alinhamento rotacionado,
visibilidade/exclusão/remoção/clear, padding automático/manual de constrained,
tight uma vez, escala de Scene, exports e falha restaurando posições de textos
e Axes. Incluem 24 combinações de engine/hierarquia/tamanho/DPI (100/150/200).

16 contratos foram registrados diretamente de Matplotlib 3.11.2/Agg e
comparados em testes sem importar a referência. Três comparações com Axes e
layout independentes e um atlas com escala/norte/legenda/colorbar horizontal
foram gerados e inspecionados visualmente. PNG/XML/dimensões de quatro SVGs,
textos no HTML e hashes dos seis módulos da implementação foram conferidos.
Não há igualdade de fontes, pixels ou solver. Textos livres não reservam margem;
coordenadas explícitas de rótulos globais constrained ficam sob controle do usuário.

Suíte completa: **438 testes, 6.349 subtests**, em 109,165 s. A duração da
suíte não mede ganho de performance. Wheel/sdist, instalação offline e ZIP
fonte são atualizados com código, documentação, regressões e exemplos deste lote.
GUI real/CI multiplataforma permanecem pendentes; a versão continua 0.1.0 alpha.
Veja [contrato, exemplos e limites](figure-labels.md).


## Edição de texto geográfico, annotations e rótulos de componentes

Treze regressões adicionais/59 subtests conferem posição em graus/frações,
destino xy e posição xyann independentes, troca de anncoords, callbacks finais,
setters de fonte/alinhamento, getters e ownership/remoção. Verificam offsets
em pontos físicos com Y positivo para cima em três projeções e três DPI,
recomposição de setas após edição/pan, obstáculos de labels e SVG/HTML.
Offsets lógicos antigos em pixels continuam preservados e documentados como
distintos da convenção Matplotlib. Estilo inválido não altera parcialmente
título de legenda ou rótulo/padding/loc de colorbar.

19 estados foram registrados diretamente de Matplotlib 3.11.2/Agg e
comparados em testes sem importar a referência. Duas comparações de mapas
antes/depois usam Axes independentes; dois exemplos próprios acrescentam
legenda/escala/colorbar horizontal. PNGs, XML/dimensões de quatro SVGs,
textos HTML e hashes dos módulos de implementação foram auditados. Inspeção
visual confirmou os exemplos finais; fontes/clipping/setas não são idênticos.

Suíte completa: **451 testes, 6.408 subtests**, em 107,249 s. A duração da
suíte não mede performance. Wheel/sdist e ZIP fonte atualizados; instalação
offline valida os novos handles e exemplos SVG/HTML sem Pillow/Matplotlib/GIS.
PNG do wheel com Pillow confronta o exemplo próprio verificado. GUI real/CI
continuam pendentes e a versão permanece 0.1.0 alpha.
Veja [contratos e limites](text-edits.md).

## Viewer Tk real, eventos e distribuição

Oito regressões adicionais/12 subtests verificam roda fracionária/zero,
coordenadas, cursor, evento fora dos Axes, renderer, edição da lista de callbacks,
debounce e cleanup mesmo com callback de fechamento reentrante/com erro.
Quatro deltas Windows, dois botões Linux e duas emissões de callbacks foram
registrados de TkAgg real e comparados sem importar Matplotlib na suíte.
Canvas sem GUI e Tk preservam a lista capturada no início da emissão.

Os dois smokes Tk passaram localmente em Windows/Python 3.14.4/Tk 8.6.
O smoke ampliado confere nove cenários usando widgets/event loop reais,
janelas ocultas e inputs sintéticos. Save escreve PNG/SVG reais com diálogo
substituído; navegação recompõe cena/componentes e eixos compartilhados.
Isso não prova aparência/input nativo nem comportamento de Linux/macOS.

Suíte completa: **459 testes, 6.420 subtests**, em 104,572 s; duração não mede
ganho de performance. CI configurada para 15 combinações de sistema/Python,
build/instalação limpa do wheel e três jobs Tk adicionais. Resultados remotos
continuam pendentes; nenhum critério da 0.2.0 é declarado fechado.
Veja [escopo, reprodução e limites](viewer-validation.md).

Instalação offline em ambiente novo confirma o wheel sem Pillow/Matplotlib/GIS,
com SVG/HTML, dados/fontes e componentes editáveis. Outro ambiente separado
com Pillow 12.3.0, sem Matplotlib/GIS, executou os dois smokes desktop em modo
isolado com importação a partir do wheel. Os pacotes wheel/sdist e ZIP fonte
incluem o lote atual; código, relatórios, documentação e CI são auditados.

## Teclado, mouse, transições e atalhos editáveis

Onze regressões adicionais/133 subtests verificam a normalização de input,
coords inteiras/geográficas, modificadores/botões, tecla durante motion,
release, duplo clique/meio, restrição de zoom e campos Tk não aplicáveis
em Configure. Conferem keymaps prospectivos/copias/contexto/desativação,
distinção de caso/modificadores, atalhos no mapa sob o cursor e ciclos de grade.

Matplotlib 3.11.2/TkAgg forneceu diretamente 60 teclas, 36 estados de máscaras,
15 botões, dez transições, oito passos de grade e dez keymaps. A execução foi
em Tk real oculto no Windows; tabelas Linux/macOS foram chamadas substituindo
o identificador de plataforma, sem declarar testes nativos nesses sistemas.
Os smokes próprios agora cobrem doze cenários com widgets/event loop reais
e inputs/diálogo sintéticos. A grade continua opcional.

Suíte completa: **470 testes, 6.553 subtests**, em 111,398 s. Duração não mede
ganho de performance. MouseButton público e exemplo com Ctrl+clique e
componentes alternáveis individualmente acompanham a entrega. Hierarquia
completa de eventos, picking, input/aparência nativa e CI remota permanecem
pendentes; não se fecha critério da 0.2.0. Veja [input](viewer-input.md).

O wheel atualizado passou no smoke offline em ambiente novo sem Pillow/GIS/
Matplotlib, incluindo MouseButton/keymaps e SVG/HTML. Em ambiente isolado com
Pillow e sem Matplotlib/GIS, passaram ambos os smokes Tk e o exemplo de
callbacks: quatro componentes alternados independentemente, Ctrl+clique
editando annotation e exportação SVG. Wheel/sdist/ZIP fonte atualizados e
auditados com os módulos, fixtures, documentação e exemplo finais.

## RGBA direto, ownership e medições desktop

Cinco regressões adicionais/33 subtests verificam o raster RGBA independente,
pixels e bytes PNG idênticos ao snapshot próprio anterior em 27 cenas,
fechamento no sucesso/erro de gravação e preservação de streams do chamador.
Renderizar RGBA não chama codificação/decodificação PNG. O smoke Tk passou
com 13 cenários: abertura sem codec/cópia inicial e liberação da imagem anterior
também são verificadas. Passaram o smoke Artist e o exemplo de callbacks,
com componentes alternados independentemente e annotation editada.

Suíte completa: **475 testes, 6.586 subtests**, em 112,530 s; essa duração não
é benchmark. A comparação desktop separada usou 16 workers novos seriais,
sete operações/quatro casos-DPI e 112 registros, todos com pixels/vistas
idênticos. Memória local diminuiu; os tempos variaram nos dois sentidos.
Veja [metodologia, amostras e limites](viewer-performance.md).

Os testes usam Tk real oculto e inputs sintéticos. Pintura/input nativo,
bases detalhadas reais e CI efetivamente executada nas outras plataformas
continuam pendentes. A versão permanece 0.1.0 alpha.

O wheel deste lote passou na instalação offline em ambiente novo sem Pillow,
Matplotlib ou GIS. Em outro ambiente isolado com Pillow e sem Matplotlib/GIS,
passaram os dois smokes Tk, o exemplo de callbacks e os cinco testes de imagem
RGBA/PNG importando o pacote instalado. Dados/fontes, exports SVG/HTML e
componentes editáveis continuam funcionais. Os relatórios do source e do wheel
registram os 13 cenários desktop; isso não substitui aparência/input nativo.

## Visibilidade e ciclo de vida de componentes

Doze regressões adicionais/18 subtests conferem desconexão de colorbar local,
escala/overview/orientação substituídos, ticks descartados em eixos/mapas
compartilhados, norm versus clim/orientação, texto interno ocultável, validação
antes de substituir e redraw observando o estado completamente registrado.
Nove contratos foram registrados diretamente de Matplotlib 3.11.2/Agg; cinco
coincidem e quatro diferenças de ownership/clear/handles/stale são documentadas.

Suíte completa: **487 testes, 6.604 subtests**, em 112,952 s; não é benchmark.
Passaram os smokes de viewer (13 cenários), Artist e exemplo de callbacks. O
novo smoke de lifecycle passou sete cenários adicionais em Tk real oculto com
edições programáticas. PNG/SVG/HTML do exemplo antes/depois foram gerados;
os dois PNGs foram inspecionados e o ponto próximo à rosa foi reposicionado.
Não se declara aparência/input nativo, CI remota executada ou critério da 0.2
fechado. Veja [contratos e limites](component-lifecycle.md).

O wheel passou no smoke ampliado de instalação offline em ambiente novo sem
Pillow/Matplotlib/GIS. Em ambiente isolado com Pillow e sem Matplotlib/GIS,
passaram os três smokes Tk, o exemplo de callbacks e os 12 testes novos
importando o pacote instalado. Os relatórios de source/wheel registram os sete
cenários adicionais. Wheel/sdist e ZIP fonte incluem os módulos, regressões,
fixtures, relatórios, exemplo/exports, documentação e CI configurada deste lote.

## Lote ampliado: dimensões, títulos, composição e abertura

Suíte completa: **504 testes, 6.705 subtests**, em 113,910 s; duração de teste,
sem afirmação de desempenho. Os 17 testes adicionais/101 subtests abrangem
dimensões/DPI, três títulos independentes, contratos registrados da referência,
registro/recuperação do primeiro draw e composição. Os 54 casos próprios
completaram sem warning ou overflow medido, em três tipos de composição,
dois layouts, três tamanhos e três DPIs. A referência teve 45 conclusões,
18 warnings e nove erros no roteiro aninhado/constrained específico; veja
[metodologia e limites](sizing-composition.md).

Passaram quatro smokes Tk: Artist, viewer (13 cenários), lifecycle (sete)
e composição/abertura (14). O exemplo de callbacks também passou. São
janelas reais ocultas e entradas/edições programáticas. Os três PNGs da galeria
foram inspecionados, com fonte menor explicitamente aplicada nos mapas pequenos
para separar títulos. Dois pares reais próprios/Agg foram conferidos lado a lado.
Há diferenças de layout e métricas; não se declara igualdade visual da janela.

O wheel passou em ambiente novo offline sem dependências opcionais, conferindo
dimensões/DPI/títulos, SVG/HTML e dados/fontes. Em ambiente isolado com Pillow
e sem Matplotlib/GIS, passaram os quatro smokes, o exemplo e os 17 testes novos
importando o pacote instalado. Relatórios source/wheel e comparações históricas
preservadas acompanham a distribuição. CI remota e conferência nativa continuam
pendentes; versão 0.1.0 alpha mantida.

## Lote ampliado: séries, ciclos, folhas de estilo e legendas

Suíte completa: **525 testes, 6.749 subtests**, em 119,285 s; não é benchmark.
As 21 regressões/44 subtests adicionais conferem múltiplos grupos e matrizes,
lookup data, atomicidade de formas/labels/estilos, ciclos condicionais/separados,
arrays opcionais, folhas locais/stacks/contextos e defaults/textos de legenda.
Contratos válidos selecionados de séries/ciclos e contextos/folha/legenda
coincidem com os estados registrados de Matplotlib 3.11.2/Agg após normalizar
grafia RGB/hex. A diferença de ciclo após erro foi medida e documentada;
não há equivalência completa de Line2D/Cycler/rcParams/handles de legenda.

Passaram os cinco smokes Tk e o exemplo de callbacks, em source e no wheel
instalado. O smoke novo cobre 12 cenários claros/escuros, com 48 colunas
sintéticas, redraw agrupado, vistas compartilhadas e histórico. Janelas reais
estão ocultas e entradas/edições são programáticas; não há teste de aparência
nativa, input físico ou desempenho em base urbana. Os quatro PNGs antes/depois
e os dois pares próprios/Agg foram conferidos; fontes da legenda conservam
o contexto de criação, inclusive após a materialização tardia de seus textos.
Métricas/layout e visibilidade dos símbolos da legenda ainda diferem.

O wheel passou em ambiente novo offline sem Pillow, NumPy, Matplotlib ou GIS,
incluindo séries/ciclos/contexto escuro, legendas e exportação SVG/HTML. Em
ambiente isolado com Pillow, sem NumPy/Matplotlib/GIS, passaram os cinco smokes,
o exemplo e os 21 testes novos (um teste NumPy pulado; ele passou no source).
Relatórios source/wheel, fixtures, folha de estilo, exemplos, docs e CI
configurada acompanham os pacotes. CI remota e conferência nativa continuam
pendentes; 0.1.0 alpha mantida e nenhum critério da 0.2 declarado fechado.
