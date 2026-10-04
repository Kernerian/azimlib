# Ticks menores e grade menor

```python
import azimlib as azl
from azimlib.ticker import MultipleLocator, AutoMinorLocator

fig, ax = azl.subplots(projection='mercator')
ax.state('SP')
ax.xaxis.set_major_locator(MultipleLocator(2))
ax.yaxis.set_major_locator(MultipleLocator(2))
ax.xaxis.set_minor_locator(AutoMinorLocator(4))
ax.yaxis.set_minor_locator(AutoMinorLocator(4))
ax.tick_params(which='minor', length=2, width=.6)
ax.grid(True, which='major', linewidth=.5)
ax.grid(True, which='minor', linewidth=.25, linestyle=':')
fig.savefig('state.svg')
azl.show()
```

`ax.minorticks_on()` habilita subdivisões automáticas nos dois eixos;
`minorticks_off()` instala NullLocator para os menores. Não habilitam grade.
Os menores vêm desligados por padrão e usam NullFormatter: não há números
adicionais até fornecer um formatter ou labels. O tamanho padrão é 2 pontos,
com largura .6, independentemente dos maiores (3.5 pontos/.8).

## Posições e textos editáveis

`AutoMinorLocator(n)` divide o intervalo entre maiores em `n` partes: `n=4`
produz três posições intermediárias. Precisa de maiores uniformes e escala
linear. Sem `n`, consulta `xtick.minor.ndivs`/`ytick.minor.ndivs`; `'auto'`
escolhe 5 partes para passos cuja mantissa é 1, 2.5 ou 5, e 4 nas demais.
O objeto depende do contexto do Axis, portanto não oferece `tick_values`
isolado. Zoom e mudança do locator maior recalculam os menores.

`set_minor_locator`, `set_minor_formatter`, `get_minor_locator`,
`get_minor_formatter` e `get_minorticklocs` estão nos objetos Axis.
`ax.set_xticks(..., minor=True, labels=...)` retorna textos editáveis;
`ax.get_xticks(minor=True)` consulta as posições. O mesmo vale para Y.
Posições que coincidem com maiores são removidas, com tolerância relativa ao
intervalo da vista. `axis.remove_overlapping_locs=False` desativa essa filtragem.
Custom locators continuam sujeitos ao limite de 1.500 posições.

## Estilos, grupos e grade

`tick_params(which='major'/'minor'/'both')` controla grupos separados.
`grid(which=..., axis='x'/'y'/'both')` controla grupos/eixos independentemente,
com estilos preservados após ocultar e mostrar. Sem argumentos, alterna
somente a grade maior. Propriedades de estilo implicam `visible=True`, como
na referência; `grid(False, color=...)` avisa e habilita.

A grade menor não cria ticks menores: habilite-os separadamente. Sem `step`,
a grade acompanha as posições do grupo escolhido. `step=` explícito permanece
uma extensão para graticule independente dos locators. Desligar ticks menores
também remove a grade baseada nesses ticks; uma grade com `step` fixo independe
deles. A visibilidade do artista retornado por grid também pode ser editada.

rcParams disponíveis: `xtick.minor.visible/size/width/pad/ndivs` e equivalentes
Y, além de `axes.grid.which/axis`. `clear()` reaplica os defaults do contexto.
Ainda não há objetos Tick completos, `tick_params(reset=True)` ou todas as
propriedades de grade por tick presentes no Matplotlib.

## Colorbars horizontais e verticais

```python
bar = fig.colorbar(layer, ax=ax, orientation='horizontal')
bar.minorticks_on()
bar.ax.tick_params(which='minor', length=2, width=.6)
bar.minorlocator = MultipleLocator(5)
bar.set_ticks([5, 15], minor=True, labels=['baixo', 'médio'])
bar.minorticks_off()
```

Colorbars oferecem `minorlocator`, `minorformatter`, `get_ticks(minor=True)`
e `set_ticklabels(..., minor=True)`. Os menores só pertencem ao eixo longo;
funcionam também por cax e nas duas orientações. Norm linear começa sem
menores, salvo rcParams explícitos. LogNorm fornece subdivisões 2–9 por
década por padrão, como na referência instalada. `minorticks_on()` seleciona
AutoMinorLocator para norm linear e LogLocator para logarítmica; a filtragem
de coincidências em log usa distância logarítmica.

Alterar clim preserva os controles menores; outra norm restaura os padrões.
O formatter menor padrão é NullFormatter, também em LogNorm nesta versão:
o LogFormatterSciNotation e suas regras de rótulos científicos ainda não
foram implementados. LogLocator tem um subconjunto de parâmetros e ainda
não reproduz toda a escolha de stride/fallback de décadas do Matplotlib.

## Exportação e referência

PNG e SVG usam a mesma cena. O desktop recompõe os ticks a partir da vista.
No HTML Mercator/equiretangular, AutoMinor/Multiple/Fixed/NullLocator e
formatters portáteis preservam grupos maiores/menores, lados, direção,
comprimentos, cores, rotação e estilos de grades durante zoom. Home restaura
a cena original. Outras projeções, funções Python e formatos customizados
precisam do desktop para recomposição completa. Textos com estilo individual
e transforms/fontes fora do subconjunto podem diferir após navegar no HTML.
Veja também as [restrições de ticker](ticks.md).

`examples/minor_ticks.py` gera [São Paulo](../gallery/minor-grid.png),
[colorbar horizontal](../gallery/minor-colorbar-horizontal.png) e
[LogNorm](../gallery/minor-colorbar-log.png), todos com SVG e HTML.
O campo colorido é sintético e não representa uma medida geográfica real.

`tools/inspect_minor_ticks.py` compara seis configurações de AutoMinorLocator
e quatro colorbars contra Matplotlib 3.11.2. Valores em
`minor-ticker-reference.json`; testes normais usam a fixture sem importar
Matplotlib. Isso verifica esses casos controlados, não equivalência integral
de escalas, offsets, todas as opções de ticker ou igualdade de pixels.
