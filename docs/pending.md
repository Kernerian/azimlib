# Inventário de pendências

O corte [0.2.0 está encerrado](release-acceptance.md), 54/54. Este é o roteiro de crescimento posterior, não uma lista de bloqueios da versão. Conferência visual humana nativa Linux/macOS permanece posterior, no escopo de plataforma documentado; CI e aceite visual Windows concluídos. Urbano e 3D/tempo continuam neste roteiro.

Estado desta fundação 0.1.0 alpha. Esta lista reúne o trabalho conhecido para
aproximar a experiência do Matplotlib e ampliar a cartografia. Não significa
que cada função de todos os toolkits Matplotlib será necessária à Azimlib.
Novas exigências e casos reais poderão acrescentar itens.

**16 é o número de frentes amplas, não a quantidade de tarefas restantes.**
Cada frente reúne entregas já feitas e trabalho pendente; a contagem só diminui
quando uma frente inteira é encerrada. Índice/culling/cache de paths, edição de
campos/scatter, GridSpec, componentes e lotes de cores são avanços dentro dessas
frentes. O progresso para o corte atual aparece nos [critérios da 0.2](release-0.2.md).
Subpassos efetivamente encerrados e as lacunas de aceitação estão no
[registro de progresso](release-progress.md): 44/54 concluídos, dez abertos,
incluindo dois aceites. O [passo 1 está aceito](artist-acceptance.md) no
catálogo 2D, com integração e auditoria 1.10–1.12. Expansões descritas abaixo
não reabrem esse corte. O [passo 2 também está aceito](layout-acceptance.md)
nos cenários de composição, textos e componentes documentados. O
[passo 3 está aceito](viewer-visible-acceptance.md), incluindo a verificação visual Windows do viewer/pan. A auditoria recente de números,
fontes, tracejados e edições integradas está [documentada](artist-validation.md).
Aliases, novas composições, LRU de raster no Tk e medições municipais reais
foram acrescentados no [lote maior](larger-batch.md). Isso já reduz o trabalho
nas frentes existentes; primeira rasterização densa e CI efetiva permanecem.

O [lote municipal de cobertura](municipal-raster.md) reduz cálculos repetidos
da rasterização com pixels preservados nos cenários medidos. O avanço é
incremental: o tempo inicial denso continua uma pendência para a 0.2.

O [lote de contornos e integração](stroke-kernels.md) amplia kernels pequenos,
corrige linhas coincidentes seguindo o contrato Agg selecionado e verifica
globo/terreno no Tk. São subpassos concluídos; CI efetiva e pintura/input físico
continuam necessários para encerrar a validação da versão.

## 1. Acabamento visual e exportação

Refinar rasterização de curvas, caps/junções, clipping fracionário, hinting e
posições subpixel de fontes. Ampliar comparações com os mesmos dados/fontes/DPI
e baselines PNG/SVG de mapas completos. Acrescentar exportação PDF vetorial e
políticas mais completas de metadata, transparência e fontes. PNG/SVG já são
funcionais; igualdade de pixels com Agg ainda não existe.

## 2. Axis, ticks, escalas e unidades

Formatters logarítmicos completos, escalas extensíveis,
unidades e datas; localizar graticules nas bordas curvas das projeções.
Ticks maiores/menores e grades independentes,
locators/formatters, longitude/latitude/DMS e controle de colorbar já existem.
Escalas não lineares comuns precisam de um contrato compatível com a semântica
geográfica; LogNorm em cores não torna a latitude logarítmica.
Offsets científicos, precisão comum, locale, texto editável de offset e
prefixos SI foram entregues; veja [formatação](numeric-formatting.md).
MathText/TeX, offsets de EngFormatter e recomposição científica HTML ainda faltam.

## 3. Layout e composição

GridSpec raiz com spans/pesos e medição automática já foi entregue; veja
[composição com spans](gridspec.md). Grids/mosaicos aninhados e seu solver
também foram entregues; veja [hierarquias](nested-layout.md). Ainda faltam
múltiplos grids raiz independentes no solver, SubFigure e layout
compressed. Expandir o solver atual para esses casos,
textos livres da Figure e obstáculos de cax/add_axes. Rótulos globais
supxlabel/supylabel e suptitle posicionável com reservas de bordas já foram
entregues; veja [rótulos globais](figure-labels.md). Melhorar a medição e a
convergência em casos difíceis sem mover eixos de posição explícita.
Eixos compartilhados, união dos dados, tickers e label_outer já foram entregues;
veja [grupos de mapas](shared-axes.md). O vínculo HTML cilíndrico, aspecto e
histórico global foram entregues; veja [navegação portátil](portable-navigation.md).
Escala/norte/rosa acompanham a navegação HTML cilíndrica. Faltam outras
projeções, recomposição geral dos componentes no HTML e navegação Tk em bases densas,
além de expandir unidades/escalas/Transforms.

## 4. Artists e API

Expandir a base comum Artist para Line2D/Patch/Collection e propriedades
completas. Ownership, stale propagation, callbacks, setp/getp e ion/ioff já
existem; relim/autoscale_view e margens recompõem os limites quando solicitados,
preservando vistas manuais. Scatter já permite editar offsets/tamanhos/array;
imagem/mesh/vetores também têm setters de dados, extent, UVC e origens.
Lotes norm/cmap/clim/array já funcionam junto de dados/estilos; veja
[edição agrupada](mappable-batches.md). Dados/estilos de linhas em lote,
marcadores/caps/junções e ContourSet/rótulos individuais já foram entregues;
veja [contratos](lines-contours.md). Posição de MapText/Annotation, destino xy/xyann e rótulos de legenda/colorbar
coerentes após edição já foram entregues; veja [texto editável](text-edits.md).
Ainda ampliar propriedades gerais e
auditar as integrações restantes. Substituição de componentes locais,
desconexão de colorbars/ticks antigos e visibilidade de texto interno foram
consolidadas; veja [ciclo de vida](component-lifecycle.md). Ainda faltam
contourf/paths públicos e atualização incremental. Cortes inline reversíveis,
valores de cor por nível e colorbar de isolinhas já estão disponíveis.
Seleção de figura por número/nome e sca já foram entregues, junto de limpeza
e subplot_mosaic plano; veja [organização de mapas](figure-state.md).
Ainda ampliar integração com event loops;
gaps NaN/máscaras e converters de unidades em plot. Múltiplos grupos, matrizes
por coluna, nomes via data e ciclos condicionais foram entregues; veja
[séries e estilos](series-styles.md). Não aceitar parâmetros ainda
não implementados silenciosamente. Manter `import azimlib as azl`.

## 5. Transformações

Grafo componível entre coordenadas geográficas, projetadas, Axes, Figure e
display, inversas, transformações combinadas e unidades físicas. Forward,
inverse e viewport próprios já existem; ainda não há o sistema completo de
Transforms que usuários do Matplotlib podem esperar.

## 6. Legendas e colorbars

Handlers customizados, mais configurações/contratos de legenda,
normalizadores adicionais, tratamento
RGBA/mascaras e regras de atualização mais amplas. Legendas em colunas/bbox,
handles compostos, colorbar horizontal/vertical, compartilhada/cax, ticks,
extensões e edição já funcionam. Alterações pelos setters do mappable notificam
suas colorbars, incluindo mappables independentes dos Axes. Normalize compartilhado
também notifica alterações diretas de limites/clip/vcenter. Ainda ampliar
reclassificação discreta e regeneração automática de legendas temáticas.

## 7. Rótulos, texto e annotations

Texto curvado por glifo, posições mais amplas/ótimas em polígonos, repetição
em linhas longas, exclusão entre leaders, shaping complexo, tipos de caixas
e setas mais amplos, prioridade e simbologia por regras. Direção local em
linhas visíveis, colisões com annotations/insets, atributos de prioridade e
filtro por extensão foram entregues; veja [rótulos](labels.md).

## 8. Estilos, símbolos e coleções

Arquivos locais de estilo, stacks/contextos e ciclos finitos de propriedades
de linha já foram entregues. Faltam discovery/rcParams mais amplos, ciclos
completos de propriedades de outras classes, perfis científico/cartográficos,
ícones externos, símbolos reutilizáveis, padrões customizados e coleções em
lote. As dez hachuras, suas repetições/combinações, marcadores e estilos básicos
já existem. Regras por atributo devem produzir legenda coerente automaticamente.

## 9. Interação e widgets

Picking/seleção de features, eventos completos/padronizados, selectors, sliders,
controles de camadas, redimensionamento e edição mais completos. Ampliar os
comportamentos de pan/zoom/histórico/save e ajustes de subplots com comparação
direta. O viewer Tk atual possui implementação própria dessas ferramentas.
Widgets/event loop reais foram validados localmente com entradas sintéticas
em janelas ocultas; veja [validação desktop](viewer-validation.md).
Teclado normalizado, modificadores/botões, transições Axes/Figure e keymaps
editáveis/ciclos de grades têm referência direta; veja [input](viewer-input.md).
Ainda falta conferência de aparência/input nativo nas plataformas suportadas.
O primeiro draw Tk já registra callbacks/canvas antes de desenhar; erro e
fechamento nesse callback têm recuperação validada. Dimensões/DPI públicos,
três títulos e 54 casos de composição também foram consolidados; veja
[contratos e limites](sizing-composition.md). Integrações densas continuam abertas.

## 10. Backends e integração

Backend Qt próprio, integração de notebook e event loop, atualização Python ↔
HTML e navegação com recomposição no navegador. O HTML atual é uma cena
exportada: não recalcula todos os componentes nem layout de rótulos ao navegar.
Manter `savefig()` estático e `show()` interativo.

## 11. Desempenho e bases densas

Ampliação do índice espacial/culling por viewport e do cache de geometrias,
simplificação com erro em pixels, fronteiras compartilhadas e renderização
incremental/em lote. Medir composição, labels, raster, I/O e memória
separadamente. Raster por tiles e cobertura fracionária já existem; bases
detalhadas de municípios ainda precisam de testes de escala e benchmarks.
Mapas completos já têm medições por etapa, pico Python da composição e
comparação alternada do renderer com imagens idênticas; veja [desempenho](performance.md).
Memória do processo incluindo buffers nativos já foi medida em exports isolados,
junto da comparação antes/depois da reutilização/liberação de buffers PNG.
Composição e redução BOX em faixas também foram entregues para fontes grandes,
com redução local de pico medida e preservação dos bytes PNG; o canvas completo
e a cobertura Python continuam existindo, sem promessa geral de velocidade.
Tk usa RGBA direto e libera imagens anteriores, sem cópia inicial redundante.
[Sete operações](viewer-performance.md) têm tempo/memória comparados em quatro
casos/DPI, com pixels/vistas preservados. Os tempos variam nos dois sentidos;
faltam ampliar cenários, pintura visível e navegação de bases detalhadas reais.
Limites imutáveis, cache limitado dos bounds projetados e descarte conservador
em Mercator/equiretangular já estão disponíveis para estático/desktop. O HTML
mantém a cena completa. Há comparação de PNG e composição com base sintética;
isso não valida ainda municípios detalhados ou todas as projeções/estilos.
Índice STR próprio com caixas float64 compactas para coleções cilíndricas elegíveis, até quatro preparações
por coleção, já consulta os candidatos mantendo a ordem de pintura. Callbacks
mantêm varredura completa; estilos individuais são examinados para overscan.
Faltam ampliar o índice para labels/campos/outras projeções e medir bases reais.
Paths de linhas/polígonos nas seis projeções internas já usam cache float64
limitado, com fonte fraca e estilos/vista recalculados; veja [contrato](projected-paths.md).
Cache de cenas, rasterização em lote e renderização incremental seguem pendentes.

## 12. Robustez cartográfica

Clipping esférico generalizado, áreas maiores que um hemisfério, viewports que
cruzam ±180°, topologia, overlay, interseção/união e robustez numérica. Ampliar
projeções, CRS/datum e geodesia elipsoidal. Atualmente são seis projeções,
EPSG:4326/3857 e geodesia esférica própria.

## 13. Formatos e dados

Leitores próprios de Shapefile/DBF, KML, CSV de pontos, rasters georreferenciados
e GeoTIFF; metadados e unidades. Bases oficiais detalhadas de municípios,
rodovias, bairros, edifícios, hidrografia e navegabilidade devem ter licença,
versão e proveniência, preferencialmente em pacotes opcionais. Não inferir
navegabilidade de rios Natural Earth, nem usar downloads implícitos.
Prioridade registrada para depois: cidades/localidades, bairros, ruas e
edificações, com camadas por atributo, labels por escala e benchmarks urbanos
reais. Veja o [roteiro urbano](urban.md). GeoJSON genérico já permite desenhar
essas feições; bases e conveniências urbanas especializadas ainda são pendentes.

## 14. Raster, terreno e métodos científicos

RGB/RGBA, máscaras/NoData, resampling, contourf, triangulação e campos
irregulares; aprofundar heatmap/density, fluxos e mapas temáticos. Campos
escalares, pcolormesh, isolinhas, hillshade, quiver e rotas geodésicas já
funcionam, com limitações descritas no [guia científico](scientific.md).

## 15. 3D e tempo

Câmera/perspectiva, clipping 3D e depth buffer próprios antes de superfícies,
terrenos ou volume 3D. Implementação planejada após a 0.2.0, junto do roteiro
urbano e das demais expansões. Artistas atualizáveis, frames, blitting e exportação
temporal/animações. São fundações futuras, não recursos disponíveis.

## 16. Documentação, testes e distribuição

Documentação versionada/hospedada, exemplos adicionais e equivalências
Matplotlib → Azimlib; ampliar regressões visuais/benchmarks e rodar CI real
multiplataforma em versões suportadas. A configuração cobre três sistemas e
Python 3.10–3.14, mas ainda não há resultados remotos. Auditar nome, licenças, dados, pacote,
semver, processo de release e publicar no PyPI. Configuração de CI, README,
guias, testes e builds existem; publicação ainda não foi feita.

Prioridade imediata: terminar as lacunas 2D de ticks/Artists/layout e medir
composição/navegação em bases densas. Novos formatos e fundações 3D vêm depois
da robustez do núcleo atual. Veja o [plano por etapas](next-steps.md).

O inventário mantém 16 frentes, com várias tarefas em cada uma. O corte da
[versão 0.2.0](release-0.2.md) possui cinco critérios próprios e não exige
concluir todo este inventário. Não há data de lançamento comprometida.
