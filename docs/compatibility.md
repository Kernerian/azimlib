# Familiaridade com Matplotlib

A referência é a organização documentada de
[pyplot](https://matplotlib.org/stable/api/pyplot_summary.html),
[Axes.plot](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html)
e da [navegação interativa](https://matplotlib.org/stable<local>/interactive.html).
O código não depende desses módulos e a semântica cartográfica pertence à Azimlib.

Use também `import azimlib as azl`: subplots, figure, show, savefig e os
controles de estado estão disponíveis diretamente. O [guia inicial](getting-started.md)
explica unidades, dados/projeção, handles e exemplos completos; o
[catálogo de reprodução](release-gallery.md) e o [registro visual](visual-differences.md)
separam evidência de API/layout de diferenças do rasterizador.

| Padrão conhecido | Azimlib 0.1 |
|---|---|
| `import matplotlib.pyplot as plt` | `import azimlib.pyplot as plt` |
| `fig, ax = plt.subplots()` | Mesmo padrão de chamada e desempacotamento |
| `fig, axs = plt.subplots(2, 2)` | `axs[0, 1]`, `axs.flat`, `axs.shape`; objeto próprio |
| `plt.figure(num)` / `get_fignums` / `close(num)` | Registro próprio por número/nome, reativação/fechamento e clear; veja [figuras](figure-state.md) |
| `plt.sca(ax)` / `fig.sca(ax)` / `plt.subplot(221)` | Seleção própria por Figure/eixo, retorno ao eixo anterior após remoção e reuso de subplot |
| `plt.subplot_mosaic('AA;BC')` | Dict de mapas nomeados, retângulos/vazios/pesos, listas 2D aninhadas e sharex/sharey booleanos |
| `plt.subplots(..., sharex='col', sharey='row')` | Grupos próprios, limites/autoescala/tickers sincronizados; estilos locais, Python/Tk e HTML cilíndrico |
| `ax.sharex(other)`, `ax.sharey(other)`, `ax.label_outer()` | Vínculo manual, consulta de irmãos, rótulos externos e remoção opcional de ticks; [regras](shared-axes.md) |
| `gs[0].subgridspec(2,2)` | Grids filhos próprios, spans/pesos e get_topmost_subplotspec; [hierarquias](nested-layout.md) |
| `ax.plot(x, y, 'r--')` | lon/lat, grupos e matrizes por coluna, nomes via data; lista de handles editáveis |
| `ax.set_prop_cycle` / `cycler` | Ciclos próprios finitos, zip/produto e defaults condicionais; azl.cycler sem dependência externa |
| `ax.scatter(x, y, s=..., c=...)` | lon/lat, tamanho nominal em pontos², cor ou sequência |
| `Normalize`, `LogNorm`, `TwoSlopeNorm`, `BoundaryNorm` | Classes próprias, escala compartilhada; retornos escalares/listas, sem MaskedArray |
| `fig.colorbar(mappable, ax=axs, cax=cax)` | Barra editável vertical/horizontal, compartilhada ou em retângulo/célula explícita |
| `mappable.set_clim`, `set_cmap`, `set_array` | Cores e barra atualizadas no próximo redraw |
| `artist.set(norm=..., cmap=..., clim=..., array=...)` / `azl.setp` | Lotes de mappables com dados/estilos validados; colorbar preserva ticks com a mesma norm e redefine ao substituí-la |
| `hatch='////'` | Dez símbolos básicos, repetição e combinações; recorte de buracos |
| `ax.imshow`, `ax.pcolormesh` | Campo escalar lon/lat; extent obrigatório ou bordas 1D, apenas shading flat |
| `ax.contour`, `ax.clabel`, `ax.quiver` | Subconjunto próprio; vetores orientados leste/norte na projeção |
| `ax.set_title`, `ax.set_xlabel`, `ax.set_ylabel` | Retornam TextArtist editável; `ax.title()` preserva encadeamento |
| `ax.set_xticks`, `ax.set_yticks`, `ax.tick_params` | Ticks maiores/menores, labels explícitos, lados, direção, tamanho, cor e rotação; `minor=True`/`which=` |
| `ax.minorticks_on/off`, `ax.grid(which=..., axis=...)` | Subdivisões automáticas e grupos/eixos com visibilidade e estilo independentes |
| `ax.xaxis.set_major_locator`, `set_major_formatter` | Objetos próprios, Fixed/Multiple/MaxN/Auto/Log/Null, funções e textos geográficos; veja [ticks](ticks.md) |
| `ScalarFormatter`, `EngFormatter`, `ticklabel_format`, `get_offset_text` | Precisão/escala científica/offset automático ou forçado, prefixos SI e texto editável; sem MathText/TeX ou offset de engenharia |
| `ax.spines['top'].set_visible(False)` | Bordas independentes com cor, largura e visibilidade |
| `ax.legend(handles, labels, ...)` | Colunas, handles compostos, best/bbox_to_anchor, textos/frame editáveis; heurística de best própria |
| `plt.rcParams`, `plt.rc_context`, `plt.style.context` | Subconjunto validado; opções desconhecidas geram erro |
| `ax.set_xlim`, `ax.set_ylim` | Limites geográficos em graus; inversão não suportada |
| `ax.grid`, `ax.legend`, `ax.text`, `ax.annotate` | Subconjunto explícito de parâmetros |
| `fig.savefig` | SVG e PNG estáticos, sem UI; PDF ainda não |
| `plt.show()` | Janela desktop Tk própria; bloqueia até fechar, como pyplot |
| `plt.show(block=False)` | Abre sem bloquear; event loop deve continuar ativo |
| `fig.show()` | Janela desktop própria, não bloqueia por padrão |
| `fig.show(backend='browser')` | Alternativa HTML explícita, offline |
| `fig.canvas.draw_idle()` | Recalcula a figura desktop após editar artistas |
| `fig.canvas.mpl_connect()` | Eventos de mouse, teclado, desenho e fechamento |
| `line.set_color`, `set_linewidth`, `set_alpha` | Métodos familiares nos artistas próprios |
| `line.set(data=..., marker=..., dash_capstyle=...)` | Dados/estilos em lote, markers e caps/junções separados; [contrato](lines-contours.md) |
| `ContourSet.set(linewidths=..., linestyles=...)` / `ax.clabel` | Estilo/valores por nível, rótulos editáveis, cortes inline reversíveis e colorbar de linhas; posicionamento/cortes e set_array têm diferenças documentadas |
| `fig.add_gridspec(...)` / `fig.add_subplot(gs[:, 0])` | GridSpec/SubplotSpec próprios com spans/pesos; raiz única no solver automático; veja [GridSpec](gridspec.md) |
| `fig.add_subplot(111)` / `fig.add_subplot(2, 3, (2, 6))` | Célula ou span em grid, índices numéricos one-based |
| `fig.subplots_adjust` | Margens e espaçamento proporcionais |
| `fig.tight_layout` / `layout='tight'` / `layout='constrained'` | Solver próprio por limites reais de texto/componentes, para um GridSpec raiz com spans/pesos; veja [layout](layout.md) |
| `fig.set_layout_engine` / `get_layout_engine` | Engines próprios, padding editável, modo inativo e controle manual |
| `artist.set_in_layout(False)` | Exclui do cálculo de margens, mantendo visibilidade independente |
| `text.set_rotation_mode(...)` | default/anchor/xtick/ytick, regras de alinhamento por caixa/âncora/ângulo; [referência](text-rotation.md) |
| `ax.tick_params(labelrotation=...)` | Major/minor, X/Y e eixo longo da colorbar; extensão labelrotation_mode seleciona o modo de rotação |
| `ax.set_xlabel(..., labelpad=4)` / `set_ylabel` | Espaço físico a partir dos ticks/offsets rotacionados; ylabel vertical usa anchor |

As extensões `map`, `states`, `rivers`, `lakes`, `coastlines`, `choropleth`,
`categorical`, `density`, `scale_bar`, `north_arrow`, `compass`, `overview`,
`zoom` e `pan` são cartográficas.
`labels` também é uma extensão: direção local, prioridades, colisões e
detalhe por extensão, com [regras próprias documentadas](labels.md).

## Desktop e comparação direta

Matplotlib **3.11.2 foi instalado em um ambiente isolado** para comparação real,
incluindo TkAgg e WebAgg. A janela padrão da Azimlib acompanha Tk: canvas branco,
tamanho 640×480, margens de subplot 0.125/0.11/0.9/0.88, título de 12 pontos,
labels de 10 pontos e toolbar inferior com Home/Back/Forward, Pan/Zoom,
Subplots e Save. Os ícones foram desenhados de forma independente.

As quatro variantes DejaVu Sans são distribuídas com sua licença original.
PNG/Tk usam essas fontes; SVG/HTML embutem as variantes utilizadas. Linhas,
marcadores e textos usam pontos convertidos pelo DPI. A legenda usa avanços de
glifos e kerning da fonte, e os handles refletem as alterações de estilo.
Rasterizadores Agg e Pillow têm diferenças de antialiasing: a equivalência
visual é uma meta, não uma alegação de igualdade de pixels.

O [inventário de sistemas](matplotlib-systems.md) separa o que já existe do que
está planejado. A listagem de 894 símbolos em 27 módulos é uma referência de
escopo, não uma declaração de compatibilidade com todos esses símbolos.

O código runtime da Azimlib não importa Matplotlib. Tk e Pillow são ferramentas
genéricas de interface/raster, sem realizar o trabalho cartográfico.

Figure/MapAxes/camadas/componentes compartilham Artist, get_children/findobj,
setp/getp, callbacks e propagação de stale. ion/ioff controlam solicitações de
redesenho; show permanece explícito. O contrato de edição não inclui todas
as propriedades/classes nem replica contagens internas de callbacks. Veja
[Artists](artists.md) para os limites e a separação entre exportação e canvas.

No desktop, o histórico guarda limites geográficos de todos os subplots.
Pan/zoom atualizam esses limites e redesenham com o núcleo da Azimlib;
`savefig()` exporta a vista corrente sem controles. O diálogo Save oferece PNG/SVG.
Restrições X/Y são suportadas no arraste; mapas mantêm proporção espacial.
O minimapa só existe visualmente se `ax.overview()` for chamado.
Ele é parte da composição exportada e usa a mesma base no desktop e no HTML.
`context='brazil'` fornece um contexto independente de uma vista estadual;
sem contexto explícito, captura a extensão atual e suas camadas geométricas.

`scale_bar`, `north_arrow`, `compass`, `overview` e `colorbar` agora retornam
componentes com `set_visible/get_visible/remove`; deixaram de retornar Axes para
encadeamento. `fig.text`, `fig.suptitle` e `subtitle` retornam TextArtist. Use
chamadas separadas, conforme os [exemplos](components.md). Ocultar um grid não
troca a formatação automática dos ticks; formatters explícitos prevalecem. A legenda mantém visibilidade independente das
camadas representadas, e seu título continua opcional.

## Alternativa HTML

Home restaura todas as vistas iniciais. Back/Forward percorrem um histórico da Figure.
Pan arrasta o conteúdo; botão direito amplia durante o arraste. Zoom usa seleção
retangular; roda e duplo clique também ampliam. O minimapa mostra a extensão
inicial e a área corrente quando adicionado, podendo ser clicado para reposicionar a vista.
Grupos compartilhados sincronizam longitude/latitude em Mercator/equiretangular
contínuas, preservando aspecto. Veja [contratos e limites](portable-navigation.md).

O navegador navega uma cena vetorial já projetada. Não baixa dados adicionais
nem conversa com o processo Python. `ax.zoom()` em Python recalcula a composição;
o zoom HTML atua na cena exportada. Grade e coordenadas de borda são recalculadas
para equiretangular/Mercator; nas demais projeções a grade usa as linhas iniciais. Conicidades
sem inversa JavaScript exibem coordenadas projetadas em metros no cursor.

Em Mercator/equiretangular contínuas, a escala recompõe distância/rótulos após
pan/zoom, e norte/rosa preservam tamanho e ancoragem. Comprimento explícito que
não cabe é ocultado com aviso. Em outras projeções/vistas descontínuas, os
ornamentos dependentes da vista continuam ocultos após navegar até Home.
Para exportar mapa final com todos os ornamentos recalculados, defina os limites
com `ax.set_extent`, `set_xlim` ou `set_ylim` e chame `fig.savefig` em Python.

Ainda sem backend Qt, todos os eventos/objetos Artist do Matplotlib, atualização live de artistas após abrir HTML,
vínculo geográfico geral no HTML para projeções não cilíndricas, gaps NaN/máscaras em séries, eixos
logarítmicos, todas as opções de legendas ou todos os rcParams. Opções desconhecidas
não são aceitas silenciosamente. A compatibilidade é ampliável, não total.

Múltiplos grupos e matrizes em plot, nomes via data, ciclos próprios e folhas
de estilo locais/empilhadas foram entregues. O shorthand geográfico Nx2
permanece distinto da matriz Y isolada da referência. Veja
[séries, ciclos e estilos](series-styles.md) para contratos e limites.

## Geographic core in 0.3.0 development

The development branch adds explicit ellipsoid/UTM, regional TM, two spherical
azimuthal projections, cylindrical seam viewports and opt-in planar topology.
These are geographic contracts, not a Matplotlib datum/topology API. See
[scope and numeric tolerances](geodesy.md); published 0.2.0 is unchanged.
