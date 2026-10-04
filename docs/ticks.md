# Ticks, locators e formatters

Veja também [rotação e alinhamento](text-rotation.md): `labelrotation` usa a
caixa após girar; `labelrotation_mode` seleciona default/anchor/xtick/ytick em
major/minor, inclusive na colorbar. Os valores de ticks fixos são preservados.

A API separa **posição** de **texto**, seguindo o contrato de
[matplotlib.ticker](https://matplotlib.org/stable/api/ticker_api.html).
Os algoritmos são próprios e usam apenas a biblioteca padrão do Python.
Esta versão implementa ticks maiores e menores. Eixos geográficos
logarítmicos e offsets científicos ainda não estão disponíveis.

## Coordenadas geográficas

```python
from azimlib.ticker import MultipleLocator, LongitudeFormatter, LatitudeFormatter

ax.xaxis.set_major_locator(MultipleLocator(2))
ax.yaxis.set_major_locator(MultipleLocator(2))
ax.xaxis.set_major_formatter(LongitudeFormatter())
ax.yaxis.set_major_formatter(LatitudeFormatter())
ax.grid(labels=False, linestyle='--', linewidth=.5)
```

O locator trabalha com longitude/latitude em graus, antes da projeção. Passo
`2` significa dois graus, não dois metros nem dois pixels. Os ticks fora da
vista podem fazer parte de `get_xticks()`/`get_yticks()`, como nos locators
do Matplotlib; o renderer desenha apenas os que atingem os limites visíveis.
Mudar a vista na janela Tk recalcula posições e textos com os mesmos objetos.

`LongitudeFormatter(dms=True)` e `LatitudeFormatter(dms=True)` produzem
rótulos como `46°30′W` ou `23°33′1.8″S`. Há controle de `degree_symbol`,
`number_format`, `direction_label`, `zero_direction_label` e
`dateline_direction_label`. DMS trata o arredondamento para o minuto/grau
seguinte; ainda não oculta automaticamente campos repetidos entre ticks.
Esses dois formatters são extensões cartográficas próprias da Azimlib,
não classes fornecidas pelo Matplotlib.

Sem objetos explícitos, a seleção automática anterior foi preservada,
incluindo o passo e os rótulos geográficos sugeridos por `grid(labels=True)`.
Um formatter explícito prevalece sobre o formato sugerido pela grade.
Com `grid(step=None)`, os ticks do grupo escolhido definem a posição da grade.
`grid(step=5)` continua sendo a extensão cartográfica para uma graticule
independente, de passo fixo. A grade permanece opcional.

## Objetos disponíveis

| Posição | Função |
|---|---|
| `AutoLocator()` | seleção de passo decimal conforme espaço disponível |
| `AutoMinorLocator(n=None)` | subdivisões de intervalos uniformes entre ticks maiores |
| `MaxNLocator(nbins=5, integer=False, prune=None)` | controle do número de intervalos e das extremidades |
| `MultipleLocator(base=2, offset=0)` | espaçamento constante e origem deslocada |
| `FixedLocator([-54, -50, -46])` | posições explicitamente fornecidas |
| `NullLocator()` | nenhum tick |
| `LogLocator(base=10, subs=(1,))` | potências/subdivisões para dados positivos de colorbar |

| Texto | Função |
|---|---|
| `ScalarFormatter()` | números simples; sem texto de offset científico |
| `StrMethodFormatter('{x:.1f} km')` | campos Python `x` e `pos` |
| `FormatStrFormatter('%.1f')` | formato com operador `%` |
| `FuncFormatter(function)` | função Python `(value, position)` |
| `FixedFormatter(['A', 'B'])` | texto por posição, preferencialmente com FixedLocator |
| `NullFormatter()` | oculta rótulos, preservando ticks |
| `LongitudeFormatter()`, `LatitudeFormatter()` | graus e hemisférios, ou DMS |

`set_major_formatter('{x:.1f}')` e `set_major_formatter(function)` convertem
automaticamente strings e funções para os formatters correspondentes.
Subclasses de `Locator` e `Formatter` podem implementar `tick_values` e
`__call__`; `formatter.set_locs` recebe o conjunto antes do desenho.

```python
locator = ax.xaxis.get_major_locator()
formatter = ax.xaxis.get_major_formatter()
ax.xaxis.set_major_formatter(lambda value, position: f'{abs(value):.1f}°W')
locator.set_params(base=1)  # se o locator escolhido for MultipleLocator
fig.canvas.draw_idle()
```

Use instâncias separadas por eixo. Diferentemente da religação silenciosa
do Matplotlib, a Azimlib rejeita tentar anexar a mesma instância a outro eixo:
locators e formatters podem depender do contexto da vista. Parâmetros inválidos
e números excessivos de ticks são rejeitados antes de alocar grandes sequências.

`set_xticks(..., labels=...)` e `set_yticks` instalam FixedLocator e
FixedFormatter, preservando os TextArtists editáveis já retornados pela API.
Substituir o formatter remove esses textos explícitos. `ax.clear()` restaura
os controladores automáticos. `get_xaxis()`/`get_yaxis()` retornam os mesmos
objetos que `ax.xaxis`/`ax.yaxis`.

O [guia de ticks menores](minor-ticks.md) descreve minorticks_on/off,
locators/formatters menores, edição por `minor=True`, estilos separados,
grade por grupo/eixo, colorbars e navegação portátil.

## Colorbars

```python
from azimlib.ticker import MultipleLocator, StrMethodFormatter

bar = fig.colorbar(layer, orientation='horizontal')
bar.locator = MultipleLocator(25)
bar.formatter = StrMethodFormatter('{x:.0f}%')
bar.update_ticks()
```

Também é possível editar `bar.ax.xaxis` para uma barra horizontal ou
`bar.ax.yaxis` para uma vertical. Com `cax`, o próprio eixo fornecido delega
esses controles à colorbar. O eixo curto não oferece ticks nesta versão;
tentativas de editá-lo explicitamente geram erro. `bar.set_ticks` instala
FixedLocator e aceita textos editáveis, como antes.

Mudar `set_clim()` preserva locator/formatter personalizados. Trocar o
objeto `norm` restaura os automáticos: a consulta seguinte ou o redraw
sincroniza a barra. A regra corresponde a
[Colorbar.update_normal](https://matplotlib.org/stable/api/colorbar_api.html#matplotlib.colorbar.Colorbar.update_normal).
Trocar a orientação da mesma barra transfere os controles para o eixo longo.
Ainda não existe um registro completo de callbacks de normalização; editar
objetos diretamente pode exigir `fig.canvas.draw_idle()` em uma janela aberta.
Setters do ScalarFormatter agora invalidam o desenho. Notação científica,
offsets, prefixos SI e texto editável de offset estão descritos em
[formatação numérica](numeric-formatting.md); MathText/TeX continuam pendentes.

`format='%.1f'` e o formato numérico legado `format='.2f'` continuam aceitos;
funções legadas atribuídas a `bar.formatter` recebem só o valor. Para callbacks
com posição, use `FuncFormatter` ou `bar.ax.xaxis.set_major_formatter(...)`.

## Exportação e validação

PNG e SVG desenham os mesmos ticks; `savefig()` continua sem controles de UI.
A janela Tk recalcula o desenho em Python. O HTML exporta uma cena pronta,
sem executar callbacks Python. Em Mercator/equiretangular, ele também recalcula
um subconjunto portátil: Auto/AutoMinor/Multiple/Fixed/NullLocator, Scalar/Fixed/NullFormatter,
longitude/latitude e DMS. Funções Python, subclasses customizadas, MaxN/Log
e formatos arbitrários não são executados no HTML; nesses casos, os ticks e
a grade personalizados são ocultados durante a navegação e restaurados por Home.
Use Tk para interação completa e controle de todos os estilos desses objetos.

`examples/ticks.py` gera três exemplos. `tools/inspect_ticker.py` compara oito
configurações numéricas e três formatters contra o Matplotlib instalado,
além da regra de preservação/reset da colorbar. `ticker-reference.json` registra
os resultados. Essa comparação controlada não implica equivalência com todas
as opções de ticker, precisão, offsets, locale ou escalas do Matplotlib.
