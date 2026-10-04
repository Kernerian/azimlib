# Cores, colorbars, hachuras e campos geográficos

## Uma escala compartilhada

```python
import azimlib.pyplot as plt
from azimlib.colors import Normalize

fig, ax = plt.subplots(projection='mercator')
points = ax.scatter([-46.63, -43.17], [-23.55, -22.90],
                    c=[.4, 1.8], s=[40, 80], cmap='viridis',
                    norm=Normalize(0, 2.2))
cbar = fig.colorbar(points, ax=ax, label='Intensidade')
cbar.set_ticks([0, .5, 1, 1.5, 2])
cbar.ax.tick_params(labelsize=9, direction='out')
cbar.set_label('Intensidade (unidades arbitrárias)', fontsize=10, labelpad=4)
cbar.outline.set_linewidth(.8)

points.set_clim(0, 3)       # mapa e barra usam a mesma normalização
points.set_cmap('plasma')
fig.canvas.draw_idle()     # atualiza uma janela desktop já aberta
fig.savefig('indicador.svg')
plt.show()
```

`fig.colorbar`, `plt.colorbar` e `ax.colorbar` retornam um objeto `Colorbar`.
A orientação padrão é vertical, à direita. `orientation='horizontal'` usa a
parte inferior. Também há `location='left'/'top'`, `fraction`, `pad`, `aspect`,
`shrink`, `alpha`, `extend='min'/'max'/'both'`, `extendfrac`, `spacing`, `drawedges`,
`format` (formato numérico, string printf ou callable) e ticks explícitos.

Edite o rótulo com `set_label`, os ticks com `set_ticks(ticks, labels=...)`,
`set_ticklabels`, a aparência dos ticks com `cbar.ax.tick_params`, a borda com
`cbar.outline`, e a visibilidade com `set_visible`. `remove` devolve ao mapa
a área reservada à barra. `update_normal(outro_mappable)` troca sua fonte de
cores; ao trocar o objeto de normalização, ticks/formatador customizados são
resetados. Alterar apenas clim/paleta preserva os ticks explícitos.

`Normalize`, `NoNorm`, `LogNorm`, `TwoSlopeNorm`, `BoundaryNorm`, `Colormap`,
`ListedColormap` e `cm.ScalarMappable` são implementações próprias. Use `None`
ou NaN para dados ausentes. Normalizadores podem ser compartilhados entre
camadas. Limites fixos facilitam comparar regiões/instantes. Use `norm` **ou**
`vmin/vmax`. Na escala logarítmica, valores não positivos não são representados.

```python
from azimlib.cm import ScalarMappable
from azimlib.colors import BoundaryNorm, ListedColormap
m = ScalarMappable(BoundaryNorm([0, 10, 50, 100], 3),
                   ListedColormap(['#eff3ff', '#6baed6', '#08519c']))
cbar = fig.colorbar(m, ax=ax, spacing='proportional', drawedges=True)
```

Coropléticos permanecem classificados por padrão (`bins=5`). `bins=None` usa
cores contínuas. `set_array` modifica os valores; `set_clim`, `set_cmap`,
`set_norm`, `get_clim`, `get_cmap` e `get_array` seguem o vocabulário familiar.
Tabelas CC0 de Viridis/Plasma/Inferno/Magma têm 256 amostras RGB8 iguais às
referências quantizadas; as outras paletas da Azimlib são interpoladas.
Veja `NOTICE_COLORMAPS` para origem e licença.

## Hachuras

Todos estes padrões existem no Matplotlib. Repetir um caractere aumenta a
densidade; combinar caracteres combina padrões:

| String Python | Efeito |
|---|---|
| `'////'` | diagonais ascendentes |
| `r'\\\\'` | diagonais no outro sentido |
| `'xxxx'` | diagonais cruzadas |
| `'....'` | pontos preenchidos |
| `'----'` | horizontais |
| `'||||'` | verticais |
| `'++'` | horizontais + verticais |
| `'o'`, `'O'`, `'*'` | círculos pequenos/grandes e estrelas |
| `'/.'` | diagonais + pontos |

```python
ax.state('SP', facecolor='white', edgecolor='black', hatch='////',
         hatch_color='#315c84', hatch_linewidth=.6, hatch_spacing=12)
```

A Azimlib recorta as hachuras contra a geometria projetada usando a regra
even-odd; respeita buracos e multipolígonos. A mesma geometria vetorial é
usada no PNG e no SVG, e aparece nos símbolos da legenda. `hatch_spacing`
e `hatch_linewidth` usam pontos; `hatch_color` e esses dois controles são
extensões explícitas da Azimlib. A densidade também responde à repetição.
No HTML exportado, a navegação escala os espaçamentos da cena; o desktop
recalcula-os em tamanho físico a cada redraw.

## Campos, relevo e vetores

```python
image = ax.imshow(values, extent=(-70, -40, -35, 5), origin='lower',
                  cmap='terrain', vmin=0, vmax=3000)
contours = ax.contour(lon_centers, lat_centers, values,
                      levels=[500, 1000, 1500], colors='black', linewidth=.6)
ax.clabel(contours, fmt='%g', fontsize=8)
fig.colorbar(image, label='Elevação (m)')
ax.quiver(lon, lat, eastward, northward, scale=25, color='black')
```

`imshow` aceita matrizes **escalares** e exige extent geográfico. `pcolormesh`
aceita vetores 1D de bordas lon/lat, com `Z.shape=(len(lat)-1,len(lon)-1)` e
`shading='flat'`. Não lê GeoTIFF, imagens RGB ou imagens de satélite ainda.
`antialiased=False` é o padrão da malha para evitar frestas entre células;
`True` ativa cobertura fracionária dos preenchimentos.
Cada célula é projetada como quadrilátero; é uma representação geográfica
vetorial, não resampling de raster com metadados georreferenciados.

`contour` usa marching squares próprio, liga segmentos e resolve células
de sela pelo decider bilinear. Valores ausentes interrompem isolinhas.
`clabel` posiciona rótulos e evita colisões; inline=True recorta o caminho
sob o texto sem modificar sua fonte geográfica. Não faz texto curvo ao longo dela.
Ainda não há `contourf` nem compatibilidade com todo `ContourSet` do Matplotlib.
contour retorna ContourSet próprio com cores/linhas editáveis por nível;
clabel retorna uma lista de handles de texto editáveis. Veja os
[contratos de contornos e rótulos](lines-contours.md), inclusive inline_spacing,
visibilidade/remoção e valores por nível. fig.colorbar(contours) mostra linhas
coloridas sólidas, sem gradiente, em orientação horizontal ou vertical.

`fields.hillshade(Z, dx=..., dy=..., azdeg=315, altdeg=45, vert_exag=1)` usa
gradientes e iluminação Lambertiana própria. dx, dy e altitude devem ter
unidades consistentes, normalmente metros; linhas de Z seguem sul→norte.
Não calcula espaçamento em metros automaticamente a partir de graus.

`quiver` interpreta u/v como componentes leste/norte e calcula a direção
na projeção por uma derivada esférica. `scale` representa unidades dos dados
por largura do Axes; escala maior produz setas menores. A posição é lon/lat.
Pode receber C e colormap/normalização para cores. Não há todos os parâmetros
de Quiver, quiverkey/barbs/streamplot nem campos volumétricos 3D.

Os handles são editáveis: ScalarImage.set_data/set_extent, MeshCollection.set_array
e VectorCollection.set_UVC/set_offsets/set_scale. Arrays de imagem podem mudar
de forma mantendo o extent; matrizes de mesh preservam as bordas. Consulte
[edição de campos 2D](field-editing.md) para exemplos, ordem de origin e os
contratos específicos de get_array/set_array e atualização da vista.

## Compatibilidade que ainda falta

Colorbar tem uma API editável concreta, mas não toda a classe Matplotlib:
há barras compartilhadas entre vários Axes e eixos explícitos `cax`, descritos
no [guia de composição](composition.md). Locator/Formatter como objetos já
estão disponíveis no [guia de ticks](ticks.md). Eixo secundário, extendrect,
callbacks completos, múltiplos arrays mascarados
e todas as opções de layout ainda não estão disponíveis. Sem `cax`, `cbar.ax`
é uma fachada para ticks/rótulo/visibilidade; com `cax`, é o próprio eixo
reservado. Normalize não devolve ndarray/MaskedArray/RGBA.

Uma janela Tk aberta usa os objetos Python vivos. O HTML é uma exportação:
mudar `set_clim` em Python exige reexportar/reabrir o HTML. Alterações por
código podem ser ligadas a callbacks no desktop; não há editor de propriedades
de colorbar no toolbar, nem promessa de compatibilidade integral com cada
backend Matplotlib.

Referências diretas: [Colorbar](https://matplotlib.org/stable/api/colorbar_api.html),
[ScalarMappable](https://matplotlib.org/stable/api/cm_api.html) e
[hachuras](https://matplotlib.org/stable/gallery/shapes_and_collections/hatch_style_reference.html).
