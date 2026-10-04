# Catálogo do corte 0.2.0: Artists e edição

Este catálogo fixa o escopo dos itens **1.08–1.11** da
[checklist](release-progress.md). Descreve a API existente que será consolidada,
não uma promessa de toda a hierarquia Matplotlib. A versão ainda é 0.1.0 alpha.
Código cartográfico/renderers/Artist são próprios; a instalação de Matplotlib
é usada apenas nos tools de desenvolvimento para registrar referências.

## Famílias que entram no aceite

| Família / entrada pública | Edição coberta | Evidências e limites |
|---|---|---|
| Figure / MapAxes | figsize, dpi, posições, títulos/rótulos, limites, margens, relim/autoscale, filhos e clear | [Figuras](figure-state.md), [dimensões](sizing-composition.md), tests/test_artists.py; limites geográficos crescentes, sem inversão dos eixos |
| Layer de linhas / `plot`, `line`, `route` | set/data/xdata/ydata, cor/largura/dash, marker/face/edge/size, cap/join, alpha, label, zorder, visibilidade | [Linhas](lines-contours.md), [séries](series-styles.md), tests/test_lines_contours.py; dados geográficos finitos, gaps/NaN/máscaras de séries ainda não |
| Layer de geometria / geojson e camadas territoriais/temáticas | estilos globais e por feature, hachuras, set_array, norm/cmap/clim, visibilidade/remoção | [Dados](data.md), [mapas](map-types.md), tests/test_api.py e tests/test_mappable_batches.py; set_data não substitui coleções arbitrárias de polígonos |
| ScatterCollection / scatter | offsets, sizes, array, norm/cmap/clim, cores/bordas/marcadores, edições combinadas | [Scatter](scatter.md), tests/test_scatter_collection.py; coordenadas finitas e tamanhos/arrays compatíveis; não toda PathCollection |
| ScalarImage / imshow | matriz escalar, shape, extent, array, norm/cmap/clim e visibilidade | [Campos](field-editing.md), tests/test_field_artists.py; extent geográfico crescente, não imagem RGB/RGBA ou GeoTIFF |
| MeshCollection / pcolormesh | valores/array com shape fixo, estilos e mapping | Mesmo documento/testes; arestas retangulares fixas, sem malha curvilínea ou triangulação |
| VectorCollection / quiver | UVC, offsets com contagem fixa, scale, array e mapping | Mesmo documento/testes; componentes leste/norte, não toda Quiver/Barbs |
| ContourSet / contour | paths/levels consultáveis, colors/widths/styles por nível, mapping e visibilidade/remoção | [Contornos](lines-contours.md), [limites](contour-boundaries.md), tests/test_lines_contours.py; paths fixos, campo novo exige contour novo; sem contourf |
| ContourLabel / clabel e Layer de labels | texto/estilo/visibilidade, inline/spacing; prioridade/colisão/halo cartográficos | [Labels](labels.md), tests/test_contour_refinement.py e tests/test_label_placement.py; solver próprio, não a posição escolhida automaticamente pelo Matplotlib |
| MapText, Annotation, TextArtist | texto, fonte/peso/tamanho, alinhamento, rotação, cor/alpha, posição nos sistemas implementados, alvo/offset da annotation | [Textos](text-edits.md), tests/test_text_edits.py; sem MathText/TeX/shaping completo ou grafo geral de Transform |
| AxisComponents / ticks / Spine | major/minor, locators/formatters, texto de offset, estilos/padding/direção, bordas independentes | [Ticks](ticks.md), [formatação](numeric-formatting.md), tests/test_numeric_formatting.py; não toda Axis/Scale/units do Matplotlib |
| Legend / LegendFrame | textos/título/frame, loc, colunas, bbox_to_anchor, padding e visibilidade | [Componentes](components.md), tests/test_component_frames.py; título só quando pedido, handlers/best próprios; textos internos ocultáveis, sem remove individual |
| Colorbar / eixo/outline | orientação/local, shrink/aspect/pad, label/ticks/formatters, extend/spacing, update_normal, visibilidade/remoção | [Científico](scientific.md), tests/test_scientific.py e tests/test_contour_refinement.py; axis proxy próprio, não MapAxes completo |
| ScaleBar | comprimento/unidade, loc, fonte/cor, frame/alpha e visibilidade | [Componentes](components.md), tests/test_scale_labels.py; graduações automáticas, distância esférica local, não geodesia elipsoidal |
| OrientationIndicator / north_arrow e compass | loc, size, color, estilos suportados, visibilidade/remoção | [Orientação](components.md), tests/test_orientation.py; dois componentes independentes, extensões cartográficas |
| Overview / inset | mapa secundário, enquadramento, foco vinculado, estilos/visibilidade e remoção | [Composição](composition.md), tests/test_ornaments.py; retângulo de foco próprio, não todo toolkit inset_locator |

## Propriedades comuns e aliases

As famílias Artist oferecem ownership/get_figure, stale/callbacks,
get_children/findobj, set_visible, set_in_layout e remoção quando aplicável.
`set`, `setp`, setters específicos e `properties`/`getp` compõem o protocolo.
Consultar propriedades não implica que todas as chaves de estilo se apliquem a
todas as geometrias: por exemplo, marker é para pontos e hatch para áreas.
A [auditoria 1.11](artist-acceptance.md) rejeita propriedades desconhecidas,
aliases ambíguos e estilos incompatíveis de texto. O vocabulário de Layer
continua compartilhado: estilos conhecidos podem ficar sem efeito em outra
geometria. Não se declara uma tipagem completa da hierarquia Matplotlib.

Os aliases gerais atuais de styles.py são:

| Grafia curta/alternativa | Propriedade |
|---|---|
| lw / ls / c | linewidth / linestyle / color |
| fc / ec | facecolor / edgecolor |
| ms / mfc / mec / mew | markersize / markerfacecolor / markeredgecolor / markeredgewidth |
| size / weight / family | fontsize / fontweight / fontfamily |
| horizontalalignment / verticalalignment | ha / va |
| aa | antialiased |

Duas grafias da mesma propriedade no mesmo lote são ambíguas e rejeitadas no
normalizador geral. ContourSet acrescenta aliases por nível: colors/edgecolors,
linewidths e linestyles. Scatter usa `s` como área em pontos quadrados e `c`
como cor/valores conforme a chamada; esses são argumentos próprios da API,
não uma equivalência geral s → markersize.

Spines/outline e LegendFrame reconhecem os aliases aplicáveis de bordas.
getp resolve aliases quando não existe um getter dedicado com aquele nome;
por isso size continua representando o tamanho físico do indicador de norte.
Componentes cartográficos próprios só aceitam os controles declarados em sua
API; a tabela de aliases não promete todas as grafias em todos os componentes.

Fontfamily aceita string, não lista de famílias. Fontstyle é
normal/italic/oblique; pesos normal/bold ou múltiplos de 100 até 900. Fontsize
precisa ser positivo. Linestyle aceita nomes ou sequência própria de comprimentos
positivos, sem o par Matplotlib (offset, sequência). [Validação](artist-validation.md)
registra diferenças e escopo das edições prevalidada/não transacionais.

## Evidência e itens ainda abertos

As referências JSON de aliases, linhas/contornos, colorbars, textos/lifecycle e
validação foram produzidas com Matplotlib instalado. Testes da biblioteca leem
esses registros sem importar Matplotlib. Semelhança da API não declara igualdade
de pixels, contagem de callbacks, topology de saddles degenerados ou solver.

O catálogo **1.08**, limites **1.09**, integração **1.10** e auditoria **1.11**
estão entregues. O aceite **1.12** fecha o passo 1 neste catálogo, com
[regressões, source/wheel/Tk e limitações explícitas](artist-acceptance.md).
O [passo 2 também está aceito](layout-acceptance.md) e o
[passo 3 está aceito](viewer-visible-acceptance.md). Os passos 4–5 continuam
abertos. A [galeria do corte](release-gallery.md) e o [guia inicial](getting-started.md)
consolidam exemplos e diferenças sem ampliar este catálogo por inferência.
