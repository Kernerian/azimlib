# Azimlib

> Evidência histórica: resultados CI, tempos e hashes abaixo pertencem aos
> snapshots originais. A preparação BSD/licenças/privacidade altera arquivos;
> os checks atuais e a relação de hashes publicados estão em
> [preparação de publicação](docs/publication-readiness.md). Esses resultados não são uma nova execução CI.

**Cartografia independente em Python, com a familiaridade de `pyplot`.**

[Começar e migrar do Matplotlib](docs/getting-started.md) ·
[Galeria reproduzível do corte](docs/release-gallery.md) ·
[API pública](docs/api.md) · [Checklist 0.2.0](docs/release-progress.md)

Azimlib vem de **azimute**. Esta primeira versão funcional implementa seu próprio
modelo geométrico, leitura GeoJSON, projeções, transformações, viewport, camadas,
composição e renderização. Não importa Matplotlib, Cartopy, GeoPandas, Shapely,
pyproj, Folium nem outro motor geoespacial.

O corte de release está nos [critérios da 0.2.0](docs/release-0.2.md), com
[checklist completa por passos](docs/release-progress.md), seguida nos próximos lotes.
O [catálogo do corte](docs/artist-scope-0.2.md) fixa as famílias de Artists cobertas;
[limites dos contornos](docs/contour-boundaries.md) registra a correção de campos constantes.
O [passo 1 está aceito](docs/artist-acceptance.md): integração das camadas,
auditoria de propriedades/aliases e limites explícitos. O [passo 2 também está
aceito](docs/layout-acceptance.md): composição, textos e componentes nos cenários
documentados. O [passo 3 está aceito](docs/viewer-visible-acceptance.md), incluindo
a conferência visual do viewer Windows. O [passo 4 está aceito localmente](docs/performance-acceptance.md), com base original detalhada, aceleração opcional própria e limites explícitos. Restam cinco subpassos do passo 5 (49/54 concluídos). [5.08–5.09 verificados localmente](docs/distribution-acceptance.md); CI efetiva e conferência nativa Linux/macOS pendentes. [Guia para iniciar a CI usando só Windows](docs/ci-setup.md).
O [alinhamento de textos rotacionados](docs/text-rotation.md) foi conferido
diretamente com Matplotlib: ticks, títulos, nomes dos eixos, textos de mapa/Figure
e colorbars compartilham regras próprias de `rotation_mode`.
A auditoria de
[edição integrada de Artists](docs/artist-validation.md) tem exemplo
[antes](gallery/artist-validation-before.png)/[depois](gallery/artist-validation-after.png)
e validação no viewer Tk e no pacote instalado.

O [lote de consolidação](docs/larger-batch.md) acrescenta aliases sem ambiguidade,
composição em vários tamanhos/DPI e cache limitado de vistas no viewer Tk.
Há exemplos com colorbar [horizontal](gallery/composition-matrix-horizontal.png)
e [vertical](gallery/composition-matrix-vertical.png), além de medidas com uma
base municipal real. Vistas novas detalhadas ainda exigem rasterização lenta.

O [lote de raster municipal](docs/municipal-raster.md) reduz trabalho repetido
em círculos/limites/áreas, mantendo PNG e pixels nos casos comparados. As quatro
vistas locais melhoraram entre 6,5% e 14,7%; a rasterização inicial densa ainda
exige trabalho futuro. Esse registro histórico antecede o [aceite medido do passo 4](docs/performance-acceptance.md).

O [lote de contornos e integração](docs/stroke-kernels.md) acrescenta kernels
de áreas pequenas, corrige linhas coincidentes sem apagar marcadores explícitos
e verifica onze cenários de raster em 100/200 DPI, além de globo/terreno no Tk.

```python
import azimlib as azl

fig, ax = azl.subplots(figsize=(8, 9), subplot_kw={"projection": "mercator"})
ax.map("brazil", facecolor="white", edgecolor="black")
ax.states(linewidth=0.6)
ax.rivers(color="#1f77b4", label="Rios")
ax.set_title("Brasil")
ax.grid()
ax.legend()
ax.scale_bar()
ax.north_arrow()
ax.overview()

fig.savefig("brasil.svg")
fig.savefig("brasil.png", dpi=150)  # Pillow opcional
azl.show()                         # janela desktop interativa própria
```

O alias compacto `azl` funciona diretamente. Também funciona
`import azimlib.pyplot as plt`, com `plt.subplots(...)` e `plt.show()`,
além de `ax.title(...)` e `fig.save(...)`.

Dimensões e títulos também seguem uma interface familiar:

```python
fig.set_size_inches(8, 6)
fig.set_dpi(150)
ax.set_title("Brasil", loc="left", pad=8)
ax.set_title("Mapa político", loc="center")
ax.set_title("2026", loc="right").set_visible(False)
```

Veja [dimensões, composição e limites](docs/sizing-composition.md),
[mapa](gallery/composition-single.png), [atlas](gallery/composition-atlas.png) e
[atlas aninhado](gallery/composition-nested.png), com exportações estáticas e HTML separado.

Várias séries, matrizes por coluna e folhas de estilo também funcionam:

```python
with azl.style.context('dark_background'):
    fig, ax = azl.subplots()
    ax.set_prop_cycle(color=['red', 'blue'], linestyle=['-', '--'])
    ax.plot([-52, -48], [[-25, -24], [-22, -21]], label=['A', 'B'])
    ax.legend()
fig.savefig('trajetos.svg')
```

Veja [séries, ciclos e arquivos de estilo](docs/series-styles.md), o
[mapa claro](gallery/series-light-after.png), o [escuro](gallery/series-dark-after.png)
e a [comparação com Agg](gallery/series-dark-comparison.png).

## Instalação local

Textos usam a caixa vertical da fonte em títulos, ticks, legendas e componentes;
Latitude/Longitude aceitam `labelpad` físico. `D` e `d` são losangos distintos.
`ScalarFormatter`, `ticklabel_format` e `get_offset_text` controlam notação
científica/offsets nos eixos e nas colorbars; `EngFormatter` acrescenta prefixos SI.
Veja [texto e formatação numérica](docs/numeric-formatting.md),
[comparação de traçados/textos](gallery/series-light-comparison.png) e
[colorbar horizontal](gallery/numeric-horizontal-comparison.png).

Requer Python 3.10 ou superior. Na pasta deste projeto:

```bash
python -m pip install -e .
python -m pip install -e ".[gui]"    # desktop: Tk + Pillow/aggdraw/NumPy genéricos
python -m pip install -e ".[gui,accelerate]"  # compilação opcional do nosso kernel
python examples/quickstart.py
```

O núcleo e a exportação SVG/HTML não têm dependências externas. O desktop usa
Tk, normalmente incluído no Python oficial, e Pillow. Não é necessário
instalar Matplotlib. O pacote está preparado para distribuição; **não foi publicado
no PyPI**. O comando `pip install azimlib` será aplicável após uma publicação.

## API familiar e navegação

- `plt.figure`, `plt.subplots`, `plt.gcf`, `plt.gca`, `plt.show`, `plt.close`.
- `ax.plot(lon, lat, "r--", linewidth=2)` retorna uma lista de artistas.
- `ax.scatter(lon, lat, s=...)`, `ax.text`, `ax.annotate`, `ax.set_title`.
- `ax.set_xlim`, `ax.set_ylim`, `ax.set_xlabel`, `ax.set_ylabel`, `ax.grid`.
- `fig.savefig`, `fig.add_subplot`, `fig.subplots_adjust`, `fig.tight_layout`.
- `fig.add_gridspec`, seleções como `gs[:, 0]`, spans e proporções de linhas/colunas; veja [GridSpec](docs/gridspec.md).
- `azl.subplots(layout="tight")` ou `layout="constrained"`: margens por medidas reais de texto/componentes; veja [layout](docs/layout.md).
- `fig.savefig("mapa.png")` e `fig.savefig("mapa.svg")` criam arquivos estáticos, sem UI.
- `plt.show()` abre o viewer desktop próprio com Tk, sem backend Matplotlib.
- `fig.show(backend="browser", path="mapa.html")` abre uma alternativa HTML portátil.

O visualizador desktop próprio segue a organização da barra Tk do Matplotlib:
**Home, Back, Forward, Pan, Zoom, Subplots e Save**. O canvas padrão mede 640×480,
usa margens 0.125/0.11/0.9/0.88 e abre sem ferramenta de navegação ativa.
Há zoom pela roda, seleção retangular, atalhos h/p/o, coordenadas do cursor,
diálogo nativo de salvar PNG/SVG e histórico de vistas. A comparação direta foi
feita com Matplotlib 3.11.2 instalado em ambiente de desenvolvimento separado.
Teclado, modificadores/botões e transições do cursor seguem
[contratos registrados da referência](docs/viewer-input.md). Os atalhos são
editáveis por `rcParams['keymap.pan']`, `keymap.save` e outros; maiúsculas e
modificadores são significativos. O [exemplo](examples/viewer_events.py) conecta
Ctrl+clique a uma annotation e alterna componentes independentemente.

Legenda, colorbar, escala, norte, rosa dos ventos, grid, annotations e minimapa
são **opcionais**. Nenhum deles aparece até o usuário adicioná-lo. O minimapa
clicável é ativado por `ax.overview()` e indica a área visível com um retângulo.
O desktop recalcula geometrias, ticks e ornamentos após navegar; a alternativa
HTML navega uma cena exportada e tem limitações próprias descritas na documentação.

Escala e legenda compartilham o estilo de caixa. Rosa dos ventos e seta de norte
têm desenhos distintos e coexistem: ax.compass() não substitui ax.north_arrow().
Cada uma tem posição, tamanho, cor e visibilidade próprios. Todos esses componentes oferecem controle explícito:

```python
scale = ax.scale_bar()
scale.set_visible(False)
fig.canvas.draw_idle()

ax.state('SP')                         # um estado brasileiro
locator = ax.overview(context='brazil') # contexto sombreado + vista atual
locator.remove()
```

Os rótulos da escala adaptam sua quantidade à largura disponível, sem reduzir
a fonte ou alterar a distância representada: três valores, apenas as
extremidades ou um texto como `100 km` nos mapas mais estreitos.
Nesse modo compacto, a caixa fica mais baixa para não reservar uma linha vazia.

Veja a [lista completa de componentes e regras de visibilidade](docs/components.md)
e [exemplos de Brasil/estado/foco](examples/regions.py).

```python
ax.zoom(2)                  # zoom programático, altera os limites geográficos
ax.pan(dlon=2, dlat=0)
ax.set_xlim(-55, -40)
ax.set_ylim(-28, -15)
ax.overview(visible=True)   # inclui explicitamente o minimapa no mapa e no viewer
```

É uma API cartográfica inspirada na sintaxe do Matplotlib, **não uma implementação
de toda a API Matplotlib**. O backend Tk é nosso, com event loop próprio e
`fig.canvas.draw_idle()` / `mpl_connect()`. Ainda não inclui objetos Artist
completos, NumPy arrays de Axes ou atualização bidirecional Python ↔ HTML.
Veja [compatibilidade](docs/compatibility.md) para os limites exatos.
As diferenças restantes de rasterização, DPI e antialiasing estão explicadas
em [qualidade de imagem](docs/image-quality.md).
Pan/Zoom, dimensões físicas/hover/fontes da toolbar e cursor sobre Axes foram
ajustados pela [auditoria Tk em quatro escalas](docs/toolbar.md). O aceite da
janela visível continua pendente; há um script de comparação lado a lado.
Veja a [comparação direta a 100 DPI](gallery/render-quality-after.png)
e o [plano de próximos avanços](docs/next-steps.md).

### Componentes e sistemas

`ax.set_title()` retorna um texto editável; ticks, labels, bordas e legenda têm
controles próprios. Fontes DejaVu acompanham o pacote com licença e são embutidas
no SVG. Traçados, marcadores e textos usam pontos convertidos pelo DPI.

```python
import azimlib.pyplot as plt

with plt.rc_context({'axes.titlesize': 16, 'lines.linewidth': 2}):
    fig, ax = plt.subplots()
    ax.map('brazil')
    line, = ax.plot([-60, -50], [-20, -10], 'o--', label='Rota')
    ax.set_title('Brasil').set_color('#222222')
    ax.set_xticks([-70, -60, -50, -40])
    ax.tick_params(labelsize=9, direction='out')
    ax.spines['top'].set_visible(False)
    ax.legend([line], ['Rota demonstrativa'], loc='upper left')
```

Veja o [exemplo completo](examples/components.py) e o
[mapa de sistemas do Matplotlib](docs/matplotlib-systems.md), com implementação
atual e próximos passos para Artists, layout, transformações, eventos e cartografia.

## Geometria e dados

`geojson` aceita caminho, texto JSON, `dict`, arquivo aberto, `__geo_interface__`
e objetos geométricos nativos. Suporta Point, MultiPoint, LineString,
MultiLineString, Polygon com buracos, MultiPolygon, GeometryCollection,
Feature e FeatureCollection. Geometrias nulas são preservadas e ignoradas ao
desenhar. Entradas inválidas geram erros explícitos.

```python
ax.geojson("municipios.geojson", facecolor="white", edgecolor="black")
ax.geojson(data, style=lambda feature: {
    "facecolor": "tomato" if feature.properties.get("alerta") else "#dddddd"
})

# Dados em metros Web Mercator são transformados pelo nosso núcleo.
ax.geojson(projected_data, crs="EPSG:3857")

line = ax.line([(-50, -10), (-43, -22)], color="red", linewidth=2,
               linestyle=(8, 3, 2, 3), arrow="both", arrowstyle="stealth")
line.set(alpha=0.5, linewidth=3)
line.set_visible(False)
```

Os dados incluídos funcionam sem rede: países do mundo, Brasil com mais detalhe,
27 estados brasileiros, rios, lagos e costas. Dados de municípios e estradas
podem ser fornecidos pelo usuário. A distribuição geográfica é generalizada;
não substitui bases cadastrais oficiais. [Proveniência e licenças](docs/data.md).

## Projeções e coordenadas

Seis projeções próprias: **equiretangular, Mercator, Equal Earth, ortográfica,
Lambert conforme cônica e Albers equivalente**. Coordenadas geográficas são
sempre `(longitude, latitude)` em graus. O sistema de projeção usa metros e
preserva a proporção espacial ao ajustar o mapa à figura.

```python
from azimlib import AlbersEqualArea

projection = AlbersEqualArea(
    central_longitude=-55, central_latitude=-15,
    standard_parallels=(-10, -30)
)
fig, ax = plt.subplots(subplot_kw={"projection": projection})
ax.map("brazil")
```

As seis projeções são esféricas. O módulo CRS implementa explicitamente
EPSG:4326 ↔ EPSG:3857, com raio Web Mercator de 6.378.137 m. Não há banco geral
de EPSG nem transformações de datum. Rotas, distâncias e escalas usam geodesia
esférica; a barra de escala representa a distância local no ponto em que é
desenhada. [Matemática e limitações](docs/math.md).

## Temáticos e composição

```python
states = azl.datasets.load("states")
layer = ax.choropleth(states, values, key="postal", cmap="ocean",
                      bins=5, scheme="quantile")
ax.legend(title="População")
ax.colorbar(layer, label="Habitantes")

ax.categorical(states, "type", colors=["#1f77b4", "#ff7f0e"])
ax.scatter(lon, lat, s=areas)  # áreas proporcionais aos valores fornecidos
ax.density(lon, lat, bins=32, smoothing=1.2)

inset = ax.inset_axes((0.65, 0.7, 0.3, 0.25))
inset.map("world")
```

Choropleths suportam intervalos iguais, quantis, valores ausentes, mapas de
cores e estilos individuais. A densidade é uma grade de contagens em células
angulares com suavização gaussiana, **não densidade por km²** nem KDE geodésico.
`labels` usa métricas de fonte, prioridade global entre camadas e posições
alternativas para evitar colisões. Há títulos,
subtítulos, legendas, barra de escala, norte, rosa dos ventos, callouts, caixas
informativas, insets e vários mapas na mesma figura.

Linhas: cor, largura, opacidade, padrões de traço, caps, joins, curvas quadráticas,
setas nas duas pontas e z-order. Polígonos: preenchimento, borda, opacidade e
estilo por feature e hachuras. Marcadores: círculo, quadrado, triângulos, losango, estrela,
pentágono, hexágono, cruzes, símbolos de texto e rotação. Textos: fonte, peso,
tamanho, alinhamento, rotação, fundo e halo. Ícones de imagem ainda não foram implementados.

## Cores, hachuras e campos científicos

```python
from azimlib.colors import Normalize

layer = ax.choropleth(states, values, key='postal', bins=None,
                      cmap='viridis', norm=Normalize(0, 2.2))
cbar = fig.colorbar(layer, ax=ax, orientation='horizontal', label='Intensidade')
cbar.set_ticks([0, .5, 1, 1.5, 2])
cbar.ax.tick_params(labelsize=9)
layer.set_clim(0, 3)  # a barra acompanha a escala do mapa

ax.state('SP', facecolor='white', hatch='////', hatch_linewidth=.6)
image = ax.imshow(Z, extent=(-70, -40, -35, 5), origin='lower', cmap='terrain')
lines = ax.contour(lon_centers, lat_centers, Z, levels=[500, 1000, 1500])
ax.clabel(lines, fontsize=8)
ax.quiver(lon, lat, eastward, northward, scale=25)
```

Colorbars verticais/horizontais têm rótulos, ticks, norm e paleta editáveis,
bordas, extensões e quatro posições. Hachuras suportam `/`, `\\`, `|`, `-`,
`+`, `x`, `.`, `o`, `O`, `*`, repetições e combinações, inclusive nos símbolos
da legenda. Normalização, marching squares, hillshade e campos vetoriais
são implementados no núcleo da Azimlib. `imshow` aceita campos escalares;
GeoTIFF, RGB e visualização volumétrica 3D ainda não estão disponíveis.

Veja o [guia científico](docs/scientific.md), a [referência pública](docs/api.md)
e a [matriz de tipos de mapas](docs/map-types.md), que distingue recursos atuais
e futuros. As coordenadas de entrada são lon/lat em graus; `extent` de imagens
também é geográfico. `s` representa pontos², larguras/fontes/espaçamentos usam
pontos e `figsize` usa polegadas. Essas unidades mantêm o instinto de Matplotlib;
a projeção e a geodesia acrescentam regras cartográficas próprias.

## Galeria reproduzível

O [catálogo consolidado](docs/release-gallery.md) reúne 19 exemplos em 100/200 DPI,
com PNG/SVG estáticos e HTML separado. Para reproduzir todos, após instalar
`.[png]`, execute `python tools/release_gallery.py`. O relatório registra hashes,
fontes dos exemplos, clipping, dimensões e textos de cada exportação.
As comparações [nativas e de raster](docs/release-gallery.md) estão identificadas;
as [diferenças aceitas e verificações abertas](docs/visual-differences.md)
continuam explícitas. A janela Tk visível ainda precisa de conferência.

Os eixos aceitam objetos `ax.xaxis.set_major_locator(...)` e
`set_major_formatter(...)`, com extensões de longitude/latitude e DMS.
Colorbars têm `locator`, `formatter` e `update_ticks()`. Veja o
[guia de ticks](docs/ticks.md) para exemplos, regras de zoom e limites atuais.
Ticks menores têm controles separados: `ax.minorticks_on()`,
`tick_params(which='minor')`, `grid(which='minor', axis='x')` e
`AutoMinorLocator`. Colorbars oferecem os mesmos grupos pelo eixo longo.
Veja [ticks menores e grade menor](docs/minor-ticks.md).

Os componentes compartilham um protocolo de Artist: edição por `setp/getp`,
callbacks, ownership, `stale` e atualização do viewer com `ion/ioff`.
Linhas simples aceitam `set_data`; títulos preservam seu handle ao editar.
Veja [Artists e atualização](docs/artists.md), incluindo os limites atuais.
`item.set(norm=..., cmap=..., clim=..., array=...)` e `azl.setp` também agrupam
dados/cores/estilos, com validação antes de alterar o handle. Veja
[edição agrupada de cores](docs/mappable-batches.md).
Linhas também agrupam data/xdata/ydata com marcadores/caps/junções. Contornos
têm estilos por nível e clabel retorna uma lista de rótulos individuais
editáveis; veja [linhas e contornos](docs/lines-contours.md).
Contornos também têm valores de cor por nível, colorbars de linhas sem gradiente
e rótulos inline com folga editável e cortes reversíveis. Veja o
[exemplo integrado](examples/contour_refinement.py).
Figuras também podem ser reativadas por número/nome, com seleção explícita
do mapa ativo por sca e composição de mapas nomeados por subplot_mosaic.
Veja [organização de figuras e mapas](docs/figure-state.md).
subgridspec e mosaicos aninhados subdividem painéis em grupos de mapas;
o solver próprio ajusta a hierarquia de um grid raiz. Veja [hierarquias](docs/nested-layout.md).

Uma `Normalize` compartilhada notifica todos os mapas e colorbars quando
`norm.vmin`, `norm.vmax` ou `norm.clip` muda. Para linhas editadas, use
`ax.relim()` e `ax.autoscale_view()`; limites manuais ficam fixos. Margens
automáticas começam em 5%, com controles por eixo. Veja
[normalização e limites](docs/norm-limits.md).

`scatter` retorna uma coleção editável: `points.set_offsets(lon_lat)` e
`points.set_sizes(areas)` atualizam posições e áreas em pontos².
`points.set(offsets=..., sizes=..., array=...)` muda pontos e valores juntos;
cena, legenda e obstáculos de labels consultam os dados atuais.
Veja [coleções de pontos](docs/scatter.md).

Campos 2D também têm handles editáveis: `image.set_data(Z)` e
`image.set_extent(...)`, `mesh.set_array(Z)` e `vectors.set_UVC(U, V, C)`.
As camadas preservam identidade, normalização, colorbar e vista manual.
Veja [edição de campos](docs/field-editing.md), incluindo ordem das matrizes,
formas aceitas e diferenças de compatibilidade.

Mapas de tamanhos diferentes podem compartilhar a mesma figura:

```python
fig = azl.figure(figsize=(11, 8), layout="constrained")
gs = fig.add_gridspec(2, 2, width_ratios=[2, 1])
brasil = fig.add_subplot(gs[:, 0])
estado = fig.add_subplot(gs[0, 1])
detalhe = fig.add_subplot(gs[1, 1])
brasil.map("brazil")
estado.state("MG")
detalhe.state("SP")
```

Veja [composição com spans](docs/gridspec.md), com pesos, ajustes e limites
do solver próprio. `azl.subplots(..., width_ratios=..., gridspec_kw=...)`
também oferece controle da grade.

Mapas comparáveis podem compartilhar limites/tickers com a mesma chamada familiar:

```python
fig, axs = azl.subplots(2, 2, sharex=True, sharey=True)
for ax in axs.flat:
    ax.map("brazil", fit=False)
axs[0, 0].set_extent((-58, -38, -34, -16))
axs[1, 1].set_xlim(-54, -42)  # todos recebem o novo foco longitudinal
```

Há modos `'all'`, `'row'`, `'col'` e `'none'`, além de vínculo manual e
`label_outer(remove_inner_ticks=False)`. Camadas/estilos/ornamentos continuam
locais. Veja [eixos compartilhados](docs/shared-axes.md), incluindo autoescala,
mosaicos aninhados. O [viewer HTML](docs/portable-navigation.md) sincroniza
grupos em Mercator/equiretangular contínuas, com histórico da Figure e aspecto
preservado; outras projeções e recomposição completa têm limites documentados.

A ampliação após a 0.2.0 de cartografia urbana — cidades, bairros, ruas e
edificações — está no [roteiro urbano](docs/urban.md). GeoJSON genérico já
desenha essas feições; bases detalhadas e conveniências especializadas ainda
serão implementadas e medidas.

Legendas aceitam `ncols`, `bbox_to_anchor`, `loc='best'` e handles compostos.
Textos, título e frame são editáveis. `fig.colorbar(layer, ax=axs)` compartilha
uma barra entre mapas; `cax=fig.add_axes(rect)` reserva sua posição explicitamente.
Veja o [guia de composição](docs/composition.md), com regras e limites atuais.

| Exemplo | Conteúdo | Código |
|---|---|---|
| [Rótulos globais do atlas](gallery/figure-labels-atlas.png), [comparação tight](gallery/figure-labels-tight-comparison.png) | suptitle/supxlabel/supylabel editáveis; [contratos e layout](docs/figure-labels.md) | [figure_labels.py](examples/figure_labels.py) |
| [Textos antes](gallery/component-text-edits-before.png), [depois](gallery/component-text-edits-after.png), [comparação](gallery/text-edits-after-comparison.png) | posição/texto de mapa e annotation editáveis, título de legenda e rótulo de colorbar coerentes; [contratos](docs/text-edits.md) | [text_edits.py](examples/text_edits.py) |
| [Componentes antes](gallery/component-lifecycle-before.png), [depois](gallery/component-lifecycle-after.png) | visibilidade independente, substituição de escala/colorbar e handles descartados; [ciclo de vida](docs/component-lifecycle.md) | [component_lifecycle.py](examples/component_lifecycle.py) |
| [Mapa completo × Agg](gallery/map-quality-state-100-comparison.png), [Brasil](gallery/map-quality-brazil-100-comparison.png), [atlas](gallery/map-quality-atlas-100-comparison.png) | mesma Scene cartográfica em dois rasterizadores, 100/150/200 DPI; [limites](docs/complete-map-quality.md) | [compare_map_quality.py](tools/compare_map_quality.py), desenvolvimento |
| [Traços × Agg](gallery/style-quality-strokes-100-comparison.png), [recortes](gallery/style-quality-clipping-100-comparison.png), [hachuras](gallery/style-quality-hatches-200-comparison.png) | nove pares em 100/150/200 DPI; [escopo e diferenças](docs/style-quality.md) | [compare_style_quality.py](tools/compare_style_quality.py), desenvolvimento |
| [Atlas interativo vinculado](gallery/linked-navigation.html), [grupos](gallery/linked-groups.html) | pan/zoom sincronizados, histórico global, aspecto e grupos por dimensão | [portable_navigation.py](examples/portable_navigation.py) |
| [Componentes durante pan/zoom](gallery/portable-components.html) | escala adaptativa em km/milhas, norte e rosa com tamanho constante e ancoragem | [portable_components.py](examples/portable_components.py) |
| [Componentes](gallery/components.png) | títulos, traçados, legenda, escala, rosa e labels | [components.py](examples/components.py) |
| [Brasil](gallery/brazil.png), [estado](gallery/state.png), [foco](gallery/focus.png) | extensão, zoom e minimapa com foco preto | [regions.py](examples/regions.py) |
| [Colorbar vertical](gallery/colorbar.png), [horizontal](gallery/colorbar-horizontal.png) | Viridis, ticks e rótulo | [scientific.py](examples/scientific.py) |
| [Hachuras](gallery/hatch-catalog.png) | dez padrões, repetição, combinações e buracos | [scientific.py](examples/scientific.py) |
| [Terreno](gallery/terrain.png) | campo escalar, hillshade e isolinhas | [scientific.py](examples/scientific.py) |
| [Globo](gallery/globe.png) | ortográfica, rotas geodésicas e vetores | [scientific.py](examples/scientific.py) |
| [Legenda em colunas](gallery/legend-columns.png) | bbox externo, título e símbolo composto | [composition.py](examples/composition.py) |
| [Atlas](gallery/atlas-shared.png), [cax](gallery/colorbar-cax.png) | norm/colorbar compartilhada, eixos reservados | [composition.py](examples/composition.py) |
| [Ticks](gallery/geographic-ticks.png), [DMS](gallery/dms-ticks.png), [percentuais](gallery/percentage-colorbar.png) | objetos de localização e formatação editáveis | [ticks.py](examples/ticks.py) |
| [Atlas automático](gallery/layout-atlas.png), [legenda externa](gallery/layout-legend.png) | margens medidas, títulos, ticks rotacionados e colorbar compartilhada | [layout.py](examples/layout.py) |
| [Layout: Matplotlib × Azimlib](gallery/layout-reference.png) | comparação com os mesmos dados e estilos | [inspect_layout.py](tools/inspect_layout.py) |
| [Hidrografia Brasil](gallery/labels-brazil.png), [Amazônia](gallery/labels-amazon.png), [foco](gallery/labels-focus.png) | nomes na direção local dos rios, detalhe por vista e ornamentos opcionais | [labels.py](examples/labels.py) |
| [Rótulos e obstáculos](gallery/label-obstacles.png) | annotations/insets, prioridades e deslocamentos com leaders | [labels.py](examples/labels.py) |
| [Grade menor](gallery/minor-grid.png), [colorbar horizontal](gallery/minor-colorbar-horizontal.png), [LogNorm](gallery/minor-colorbar-log.png) | estilos independentes, subdivisões editáveis e zoom | [minor_ticks.py](examples/minor_ticks.py) |
| [Artists antes](gallery/artists-before.png), [depois](gallery/artists-after.png) | o mesmo mapa com linha, título, escala, visibilidade e colorbar editados | [artists.py](examples/artists.py) |
| [Norm antes](gallery/shared-norm-before.png), [depois](gallery/shared-norm-after.png) | uma alteração de vmax atualiza dois mapas e a barra compartilhada | [norm_limits.py](examples/norm_limits.py) |
| [Limites antes](gallery/data-limits-before.png), [depois](gallery/data-limits-after.png) | edição da rota com vista automática e manual lado a lado | [norm_limits.py](examples/norm_limits.py) |
| [Scatter antes](gallery/scatter-before.png), [depois](gallery/scatter-after.png) | posições, áreas e valores editados, com legenda/colorbar | [scatter_editing.py](examples/scatter_editing.py) |
| [Rosa e seta juntas](gallery/orientation-both.png), [só a seta](gallery/orientation-arrow-only.png) | orientação com componentes independentes, edição e visibilidade | [orientation.py](examples/orientation.py) |
| [Campos antes](gallery/fields-before.png), [depois](gallery/fields-after.png) | imagem, mesh e vetores editados, com escala de cores compartilhada | [field_editing.py](examples/field_editing.py) |
| [Cores antes](gallery/mapping-before.png), [depois](gallery/mapping-after.png) | dados, paleta, norm e limites editados em lote; mesmos handles/colorbar | [mappable_batches.py](examples/mappable_batches.py) |
| [Linhas/contornos antes](gallery/lines-contours-before.png), [depois](gallery/lines-contours-after.png) | rotas/marcadores, traços por nível e rótulos individuais editados | [lines_contours.py](examples/lines_contours.py) |
| [Isolinhas antes](gallery/contour-refinement-before.png), [depois](gallery/contour-refinement-after.png) | cortes inline, cores por nível e barras uniformes/proporcionais | [contour_refinement.py](examples/contour_refinement.py) |
| [Atlas nomeado antes](gallery/figure-state-before.png), [depois](gallery/figure-state-after.png) | Brasil/SP/AM, seleção explícita entre figuras e cores compartilhadas | [figure_state.py](examples/figure_state.py) |
| [Atlas aninhado antes](gallery/nested-atlas-before.png), [depois](gallery/nested-atlas-after.png) | Brasil, grupo de regiões e edição de pesos/títulos | [nested_atlas.py](examples/nested_atlas.py) |
| [Vistas compartilhadas antes](gallery/shared-axes-before.png), [depois](gallery/shared-axes-after.png) | político/rios/valores/rotas, uma vista comum, ticks externos; PNG/SVG | [shared_axes.py](examples/shared_axes.py) |
| [Comparação de eixos compartilhados](gallery/shared-axes-reference.png) | limites/ticks/rótulos externos com os mesmos dados/DPI em Agg/Azimlib | [compare_shared_axes.py](tools/compare_shared_axes.py), somente desenvolvimento |
| [Comparação de hierarquia](gallery/nested-reference.png) | alocação aninhada/mapas nos mesmos dados/DPI | [compare_nested_layout.py](tools/compare_nested_layout.py), somente desenvolvimento |
| [Comparação de mosaicos](gallery/mosaic-reference.png) | mapas em AA/BC com os mesmos dados/DPI em Agg/Azimlib | [compare_mosaic.py](tools/compare_mosaic.py), somente desenvolvimento |
| [Comparação de isolinhas](gallery/contour-reference.png) | Matplotlib/Agg e Azimlib, mesmos dados e DPI | [compare_contours.py](tools/compare_contours.py), somente desenvolvimento |
| [Atlas com spans](gallery/gridspec-atlas.png) | Brasil ocupa duas linhas; MG/SP ao lado, colorbar compartilhada e ornamentos explícitos | [gridspec_atlas.py](examples/gridspec_atlas.py) |
| [Escalas adaptativas](gallery/scale-labels.png) | três larguras, mesma fonte/distância, redução automática dos rótulos que colidiriam | [scale_labels.py](examples/scale_labels.py) |

Há PNG/SVG estáticos e HTML interativo dos exemplos. Dados de população,
elevação e vetores desta galeria são sintéticos e identificados como tal.
Os limites territoriais e a hidrografia vêm de Natural Earth. A figura de
hidrovias enviada exige uma base específica com navegabilidade por trecho;
a biblioteca não infere essas classes a partir de rios genéricos.

`ax.labels(data, placement='auto')` usa a direção local em linhas e procura
espaço fora de annotations, insets e componentes visíveis. `priority_field`
seleciona prioridade por feature e `min_span`/`max_span` controlam detalhe por
extensão geográfica. O desktop recalcula os rótulos a cada desenho; o HTML
navega uma cena exportada. Veja [rótulos](docs/labels.md) e o
[inventário de pendências](docs/pending.md).

## Desenvolvimento e distribuição

Benchmarks de mapas completos separam setup, composição, SVG, PNG e
recomposição após zoom. Veja [desempenho medido](docs/performance.md), com
amostras, limites da medição de memória e comparação alternada do renderer.
O PNG libera seus buffers temporários após uso e reutiliza o primeiro tile de
geometrias; a comparação de processo antes/depois preserva os bytes da imagem.
Buffers grandes usam composição e redução BOX em faixas, com comparações
de memória/tempo e PNG idêntico documentadas; o canvas completo ainda existe.
O [estado em 200 DPI](gallery/performance-state-200.png) preserva o desenho
estático e os componentes opcionais do caso medido.
Há também [reutilização do viewport e descarte conservador](docs/viewport-performance.md)
para exportação/desktop, preservando a cena completa de navegação HTML.
Coleções maiores podem usar o [índice espacial próprio](docs/spatial-index.md),
reutilizado por projeção, com preservação da ordem e dos estilos por feature.
Sua preparação STR compacta tem comparação reproduzível de tempo/consultas e
memória Python, com [resultados e limites](docs/performance.md).
O [cache limitado de paths](docs/projected-paths.md) também reutiliza coordenadas
projetadas de linhas/polígonos nas seis projeções internas, preservando estilos e precisão.

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python examples/gallery.py --output gallery --png
python examples/scientific.py
python examples/composition.py
python examples/ticks.py
python examples/layout.py
python examples/labels.py
python examples/minor_ticks.py
python examples/artists.py
python examples/norm_limits.py
python examples/scatter_editing.py
python examples/orientation.py
python examples/field_editing.py
python examples/mappable_batches.py
python examples/lines_contours.py
python examples/gridspec_atlas.py
python examples/scale_labels.py
python tools/benchmark_raster.py
python tools/benchmark_maps.py --repeats 3 --dpi 100 --memory --output maps.json
python tools/compare_raster_versions.py --repeats 4 --output comparison.json
python tools/compare_spatial_builders.py --repeats 6 --output builders.json
python tools/compare_projected_paths.py --repeats 6 --output paths.json
python -m build
python tools/smoke_installed_package.py
python tools/smoke_artist_tk.py
python tools/smoke_viewer_tk.py
python tools/smoke_component_lifecycle_tk.py
```

A suíte verifica fórmulas e inversas, áreas locais, CRS, GeoJSON, antimeridiano,
buracos em pixels, clipping, transparência, estilos, composição e navegação.
O repositório inclui configuração de CI para Python 3.10–3.14 em Windows,
Linux e macOS, com instalação isolada do wheel e jobs adicionais de Tk.
A CI remota permanece pendente. O [viewer foi validado localmente](docs/viewer-validation.md)
com widgets/event loop reais e janelas ocultas; isso não declara igualdade visual.
O Tk usa diretamente o buffer RGBA próprio; `savefig()` continua codificando
PNG/SVG estáticos, sem UI. O comparador `tools/benchmark_viewer.py` mede
abertura, redesenho, navegação, resize e edição com contadores de memória do
processo, comparando pixels/estados com o código próprio anterior.
Veja [resultados e limites das medições Tk](docs/viewer-performance.md).

[Arquitetura](docs/architecture.md) · [API e compatibilidade](docs/compatibility.md)
· [Roadmap](docs/roadmap.md) · [Changelog](CHANGELOG.md)

Código original sob BSD-3-Clause, copyright Kernerian; dados Natural Earth em domínio público; tabelas Viridis,
Plasma, Inferno e Magma sob CC0. Fontes DejaVu preservam sua licença.

O inventário possui [16 frentes pendentes](docs/pending.md), com várias tarefas
por frente. A [versão 0.2.0](docs/release-0.2.md) tem cinco critérios propostos
para consolidar o núcleo 2D; não precisa esperar formatos futuros ou 3D.
O número atual permanece 0.1.0 alpha até concluir esse corte.
