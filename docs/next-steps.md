# Próximos avanços da Azimlib

O roteiro urbano, 3D e as demais expansões fora do corte ficam para depois
da 0.2.0. A prioridade atual é consolidar e validar os recursos 2D existentes.

O objetivo é ampliar a mesma arquitetura e API, mantendo Matplotlib apenas
no ambiente de referência. Cada etapa precisa de exemplos reproduzíveis,
validação funcional e verificação visual PNG/SVG/desktop.

## 1. Qualidade visual — em andamento

Caixas verticais da fonte em textos/títulos e labelpad, geometria de marcadores
e formatação científica/offsets foram consolidados no
[lote de texto/formatação](numeric-formatting.md), com comparações diretas de
96 estados tipográficos e matriz de composição atualizada. Hinting e solver
ainda diferem; CI/aparência nativa continuam abertos.

Já corrigidos: espessura física de segmentos, cobertura de preenchimentos,
área de marcadores circulares, fundos de texto por métricas compartilhadas
e frestas em colorbars. A galeria contém uma comparação com Agg, no mesmo
canvas de 640×440, a 100 DPI e com DejaVu, gerada por compare_renderers.py.

Ainda refinar: curvas e tesselação, clipping fracionário, junções/caps,
hinting e posição subpixel do texto; comparar também mapas completos com
as mesmas bases e parâmetros. As medições de área não garantem igualdade
de todos os pixels ou de toda a interface Matplotlib.

## 2. Legendas, colorbars e layout — primeira entrega concluída

Já implementados: múltiplas colunas, bbox_to_anchor, loc='best', títulos,
textos/frame editáveis e handles compostos; cax explícito e barras
compartilhadas por vários Axes. Há três exemplos em composition.py e
verificação numérica direta com Matplotlib em composition-reference.json.

Já disponíveis também: locators/formatters como objetos, incluindo graus,
hemisférios e DMS; ticks personalizados no mapa e na colorbar. Veja ticks.md.
Ticks menores, grades independentes, offsets científicos editáveis e prefixos
SI estão disponíveis; ainda fazer: recomposição científica no HTML, handlers
customizados e normalizadores adicionais. Normalize compartilhado já tem callbacks próprios.
Layout por limites reais de títulos,
ticks, legendas e colorbars está disponível para um GridSpec raiz com spans/pesos;
veja [layout](layout.md) e [GridSpec](gridspec.md). Expandir para grids
múltiplos grids raiz independentes e layouts comprimidos. Grids/mosaicos
aninhados já estão disponíveis; veja [hierarquias](nested-layout.md).

Entrega disponível: atlas de quatro regiões com a mesma norm/colorbar,
legenda composta e barra em cax, exportados em PNG/SVG/HTML. O novo atlas
em layout.py demonstra margens automáticas, ticks rotacionados e suptitle.
O atlas em figure_labels.py acrescenta supxlabel/supylabel e edição dos textos
da Figure, com reservas em grids simples/aninhados; veja [contratos](figure-labels.md).

## 3. Rótulos e simbologia cartográfica — primeira entrega concluída

Direção local em trechos visíveis de rios/estradas, colisões com annotations,
insets e ornamentos, prioridade por atributo e etiquetas por extensão/zoom
estão disponíveis. Veja [rótulos](labels.md). A direção é de um bloco reto;
texto curvado glifo a glifo ainda não está disponível.

Entrega disponível: mapa hidrográfico em três extensões e exemplo de obstáculos,
com PNG/SVG/HTML e dados Natural Earth. Classes de navegabilidade exigem outra
fonte. Ainda fazer: busca mais ampla em polígonos, repetição em linhas,
leaders sem cruzamentos e regras de simbologia por atributo.

## 4. Navegação e bases detalhadas

Índice espacial, descarte fora do viewport, cache de projeção, simplificação
com erro em pixels e fronteiras compartilhadas. Manter histórico, escala e
minimapa consistentes após cada vista; medir tempo e memória separadamente.

Já há benchmarks de mapas completos por etapa e comparação alternada do PNG,
com ganhos locais modestos e pixels preservados. Veja [desempenho](performance.md).
A medição de zoom ainda é só recomposição Python; picos tracemalloc são somente
de composição. Exports completos já têm também contadores do processo incluindo
buffers nativos, com comparação em workers novos antes/depois da liberação e
reutilização de tiles PNG. Esses exports não medem latência GUI. O Tk tem agora
[medição própria de sete operações](viewer-performance.md), com RGBA direto,
sem retenção inicial redundante, widgets/event loop reais ocultos e inputs
sintéticos. Pixels/vistas foram preservados em quatro casos/DPI; o redesenho
ainda demora segundos. Falta ampliar cenários, culling/cache e cobertura,
inclusive com pintura visível e uma base detalhada real.
Composição de tiles grandes e redução BOX por faixas já têm regressões de
pixels e benchmarks; reduzem o pico nos casos grandes, com trade-off de tempo
documentado. Não eliminam o canvas completo nem o custo da cobertura Python.
Primeiro descarte conservador cilíndrico e cache de limites projetados entregues;
veja [viewport](viewport-performance.md). Índice cilíndrico próprio entregue,
com preparação STR e armazenamento float64 compacto medidos contra o BVH inicial;
O [cache de paths projetados](projected-paths.md) reutiliza linhas/polígonos das
seis projeções internas em armazenamento limitado. Falta ampliar indexação/cache
para outras camadas/projeções e medir navegação com base municipal real e GUI funcional.

Entrega esperada: navegação fluida em uma base detalhada de municípios,
com resultados equivalentes ao render completo sem simplificação.
O aprofundamento em cidades, bairros, ruas e edificações está registrado no
[roteiro urbano](urban.md), com contratos de dados, simbologia, rótulos por
escala e medições em bases reais.

## 5. Formatos e cartografia científica

Leitores próprios de Shapefile/DBF, KML e campos georreferenciados;
metadados de raster, RGB/resampling, contourf, triangulação e CRS adicionais.
Hillshade e campos escalares já existem; GeoTIFF e transformações de datum
ainda não estão disponíveis. As bases devem ter licença e versão explícitas.

## 6. 3D, tempo e distribuição

Para elevação/volume 3D: câmera, transformações 3D, clipping e depth buffer
próprios antes de superfícies e campos volumétricos. Para tempo: artistas
atualizáveis, frames e exportação de animações. Paralelamente: CI multiplataforma,
documentação versionada, política semver e auditoria antes de publicar no PyPI.

Este é um plano por etapas, não uma declaração de recursos já implementados.

## Fundação de Artists entregue e próximo passo

Artist comum, callbacks, propagação de stale, setp/getp e ion/ioff foram
entregues com o exemplo antes/depois. Colorbars recebem alterações pelos
setters de ScalarMappable; linhas simples permitem set_data sem mudar a vista.
Normalize compartilhado, relim/autoscale_view, margens e preservação de vistas
manuais também foram entregues; veja [normalização e limites](norm-limits.md).
Edição de posições, áreas e array de ScatterCollection também está disponível;
veja [scatter](scatter.md). Imagem, mesh e vetores têm setters próprios de
dados/geografia; veja [campos 2D](field-editing.md). Composição com spans e
GridSpec raiz também foi entregue; veja [GridSpec](gridspec.md).
Lotes norm/cmap/clim/array combinados com dados/estilos foram entregues,
com validação e notificações finais; veja [cores em lote](mappable-batches.md).
Dados/estilos de linhas em lote, marcadores/caps/junções, ContourSet e rótulos
individuais também foram entregues; veja [linhas e contornos](lines-contours.md).
Valores de cor por nível, colorbar de isolinhas e cortes inline reversíveis
também foram entregues em um lote integrado, sem alterar a geometria fonte.
Os próximos aprofundamentos são ampliar contratos de propriedades de Artists,
validar mapas completos em vários DPI e medir desempenho de composição/raster.
Depois, ampliar o grafo de transformações e SubFigure. Eixos compartilhados,
tickers/limites/autoescala em grupos e label_outer já foram entregues;
veja [grupos de mapas](shared-axes.md). O HTML portátil já integra grupos
cilíndricos, aspecto e histórico global; veja [navegação portátil](portable-navigation.md).
Escala/norte/rosa acompanham a navegação HTML cilíndrica. Faltam outras
projeções e recomposição geral dos componentes no HTML. O Tk foi validado
localmente com widgets/event loop reais em janelas ocultas e entradas sintéticas;
faltam aparência/input nativo, bases detalhadas reais e execução multiplataforma.
Veja [validação desktop](viewer-validation.md).
Mosaicos planos e seleção de figuras por número/nome/eixo já foram entregues;
veja [organização de mapas](figure-state.md). Mosaicos/grids aninhados e
composição automática hierárquica também foram entregues; veja [hierarquias](nested-layout.md).
Veja [Artists](artists.md).
Veja também o [inventário detalhado de pendências](pending.md).
Veja a [matriz atual de visualizações](map-types.md) e as
[restrições de compatibilidade](compatibility.md).
O [corte proposto de 0.2.0](release-0.2.md) reúne cinco critérios de conclusão,
sem esperar todos os recursos futuros nem prometer uma data sem validação.

Último lote consolidado: dimensões/DPI públicos, três títulos, registro do
primeiro draw e recuperação de abertura; matriz de 54 composições e 14 cenários
Tk. Próximo foco: ampliar integrações de Artists/layout em mapas densos, depois
conferência nativa e CI efetiva antes do corte de release.

Lote ampliado de séries/estilos entregue: grupos e matrizes em plot, data por
nome, ciclos próprios condicionais, folhas locais/stacks/contextos, defaults
e texto lazy de legenda estáveis. Há referência direta, 21 regressões e 12
cenários Tk adicionais. Gaps/máscaras/units, integrações densas e aparência
nativa/CI real permanecem pendentes; o corte da 0.2 não foi declarado fechado.
Veja [contratos e galeria](series-styles.md).
