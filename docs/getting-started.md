# Do Matplotlib para mapas com Azimlib

Esta é a API da fundação **0.2.0**, independente de Matplotlib/GIS. Artefatos locais disponíveis; publicação no PyPI é separada. Aceite visual Windows e CI Windows/Linux/macOS; aparência nativa Linux/macOS não conferida.
O [catálogo](artist-scope-0.2.md) delimita as famílias suportadas. Familiaridade
com Matplotlib não significa que qualquer argumento de Matplotlib já exista.

## Instalar e escolher a saída

Na raiz do projeto, com Python 3.10 ou superior:

```bash
python -m pip install -e .
python -m pip install -e ".[png]"
python -m pip install -e ".[gui]"
python -m pip install -e ".[gui,accelerate]"
```

Escolha a instalação necessária: core gera SVG e HTML sem dependências;
`png` acrescenta Pillow; `gui` acrescenta Pillow, aggdraw e NumPy genéricos,
e usa Tk do Python. Geometria, projeções, composição e estilos continuam próprios;
aggdraw apenas preenche polígonos de stroke já construídos durante a navegação.
Tk não é instalado por pip. Matplotlib não é necessário. O pacote ainda não
foi publicado no PyPI; depois da publicação, a instalação será `pip install azimlib`.
Veja [distribuição e validação](validation.md) e [proveniência dos dados](data.md).

`accelerate` é opcional: NumPy/Numba compilam o kernel de cobertura da Azimlib
para traçados longos. Não substituem geometria, projeções ou renderização por
outra biblioteca cartográfica. O primeiro raster paga importação/compilação e
o compilador ocupa memória adicional; sem ele, PNG/Tk continuam funcionando.

`savefig()` cria um arquivo estático. `azl.show()` abre o canvas desktop e
bloqueia até fechar, enquanto `fig.show()` não bloqueia por padrão.
`fig.show(backend='browser', open_browser=False, path='mapa.html')` grava a
alternativa HTML sem abrir janela; ela não mantém uma conexão com Python.
Veja [viewer](viewer-validation.md) e [limites HTML](portable-navigation.md).

## Começar sem componentes automáticos

```python
import azimlib as azl

fig, ax = azl.subplots(figsize=(6.4, 4.8), projection='mercator')
ax.map('brazil', facecolor='white', edgecolor='black', linewidth=.8)
ax.states(edgecolor='#777777', linewidth=.4)
ax.set_title('Brasil')
ax.set_xlabel('Longitude', labelpad=4)
ax.set_ylabel('Latitude', labelpad=4)
fig.savefig('brasil.svg')
azl.close(fig)
```

Adicione `ax.grid()`, `ax.legend()`, `ax.scale_bar()`, `ax.north_arrow()`,
`ax.compass()` ou `ax.overview()` explicitamente. A grade começa desativada,
e a legenda só ganha título quando `title=...` é fornecido. Norte e rosa dos
ventos são componentes diferentes; ambos podem existir juntos.

## Editar pelos handles

```python
import azimlib as azl

fig, ax = azl.subplots(figsize=(7, 5), layout='constrained')
ax.state('SP', facecolor='#eeeeee', edgecolor='#666666')
line, = ax.plot([-51, -49, -47], [-24, -23, -22], 'D--',
                color='#9467bd', markersize=6, label='Rota sintética')
title = ax.set_title('São Paulo')
scale = ax.scale_bar(length=100, fontsize=9)
north = ax.north_arrow(loc='upper left')
compass = ax.compass(loc='upper right')
overview = ax.overview(context='brazil', loc='lower right')
legend = ax.legend(loc='upper right')
line.set(linewidth=1.3, markerfacecolor='white')
title.set_text('São Paulo · componentes independentes')
compass.set_visible(False)
scale.set(length=50, fontsize=10)
ax.set_xlabel('Longitude', labelpad=6)
ax.set_ylabel('Latitude', labelpad=6)
ax.tick_params(labelrotation=35, labelrotation_mode='default')
fig.savefig('estado.svg')
azl.close(fig)
```

Em um viewer aberto, `fig.canvas.draw_idle()` solicita o redesenho depois de
uma edição. `set_visible(False)` oculta e `remove()` descarta o Artist.
Não se regenere uma legenda implicitamente ao mudar uma camada: chame
`ax.legend()` de novo se quiser reconstruir seus handles.
Textos livres/annotations podem se sobrepor; layout automático não resolve
qualquer colisão. `labels(placement='auto')` oferece a busca cartográfica
própria, com prioridade e halo. [Textos](text-edits.md),
[rotação](text-rotation.md), [labels](labels.md) e [layout](layout-acceptance.md).

## Colorbar ligada ao dado

```python
import azimlib as azl
from azimlib.colors import Normalize

fig, ax = azl.subplots(figsize=(7, 6), projection='mercator', layout='constrained')
states = azl.datasets.load('states', country='brazil')
values = [float(i) for i in range(len(states['features']))]
layer = ax.choropleth(states, values, bins=None, cmap='viridis',
                      norm=Normalize(0, 26), edgecolor='white', linewidth=.4)
bar = fig.colorbar(layer, ax=ax, orientation='horizontal', label='Indicador sintético')
bar.set_ticks([0, 10, 20, 30])
layer.set_clim(0, 30)
bar.ax.tick_params(labelsize=9)
bar.set_label('Indicador sintético atualizado', labelpad=6)
ax.set_title('Estados · valores demonstrativos')
fig.savefig('tematico.svg')
azl.close(fig)
```

A barra acompanha `norm`, `cmap` e `clim` do mappable. Há orientação vertical
e horizontal, quatro posições, `cax`, barra compartilhada, ticks major/minor,
extensões, remoção e controles do outline. O eixo da barra é um proxy próprio,
não um MapAxes completo. [Cores e colorbars](scientific.md),
[edições agrupadas](mappable-batches.md) e [normas compartilhadas](norm-limits.md).

## Os instintos que mudam

| Hábito | Regra da Azimlib |
|---|---|
| `x, y` de plot/scatter | Longitude, latitude em graus, nesta ordem; `lon=`/`lat=` também existem |
| Tamanho e estilo | figsize em polegadas, fontes/linewidth/labelpad/markersize em pontos, scatter `s` em pontos² |
| `extent` | `(west, east, south, north)` em graus, também para campos escalares; limites crescentes |
| Projeção | Seis projeções esféricas próprias; não se entrega um objeto Cartopy/pyproj |
| Aspecto do mapa | A projeção preserva proporção espacial; o quadro visível pode ocupar menos que o espaço alocado |
| `imshow(Z)` | Campo escalar 2D geográfico; ainda não RGB/RGBA, GeoTIFF ou imagem de satélite pronta |
| `quiver(U,V)` | Componentes leste/norte; a direção é calculada na projeção |
| Densidade | Contagem suavizada em células angulares, não pessoas/km² nem KDE geodésico |
| Escala | Distância esférica local na latitude/posição da barra, não uma escala uniforme de toda a projeção |
| Textos rotacionados | default alinha a caixa após rotação; anchor alinha antes; xtick/ytick escolhem alinhamento por ângulo |
| Hachuras | `/`, `\\`, `|`, `-`, `+`, `x`, `.`, `o`, `O`, `*`, repetição/combinação; geração própria |
| `plot()` / edição | Retorna lista; `line, = ...`; dados finitos, sem gaps NaN/máscaras ou inversão de eixos neste corte |
| Navegação | Tk recalcula geografia/ornamentos; HTML navega uma cena exportada e tem limites por projeção |

[Equivalências detalhadas](compatibility.md) · [matemática](math.md) ·
[tipos de mapas](map-types.md) · [reprodução da galeria](release-gallery.md).
