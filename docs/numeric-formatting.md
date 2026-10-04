# Texto, marcadores e formatação numérica

O núcleo e os renderizadores continuam próprios. Matplotlib 3.11.2 foi usado
somente como referência de desenvolvimento, inclusive para medir as caixas de
texto e os paths normalizados dos marcadores.

## Espaçamento em todos os textos

A caixa vertical usa as métricas TrueType da fonte (ascendentes, descendentes
e espaço entre linhas), ampliadas quando acentos/glifos exigem. A leitura usa
somente a biblioteca padrão Python e as fontes licenciadas incluídas no pacote.
Essa base atende títulos, nomes dos eixos, ticks, legendas, colorbars, textos
livres, annotations e ornamentos. PNG/SVG compartilham os mesmos baselines.
Títulos multilinha com alinhamento baseline ancoram a última linha; as anteriores
ficam acima. Títulos também reservam espaço para offsets no topo do mapa.

`labelpad` mede pontos entre a caixa dos ticks e a caixa do nome do eixo:

```python
ax.set_xlabel('Longitude', labelpad=8)
ax.set_ylabel('Latitude', labelpad=8)
# Default familiar: 4 pontos. Default editável para novos Axes:
azl.rcParams['axes.labelpad'] = 6
```

Os 96 estados registrados da referência cobrem dois tamanhos/pesos, texto
simples/multilinha/acentos, quatro alinhamentos e rotações 0°/90°. A maior
diferença vertical observada é 1,34 pixel lógico, por métricas/hinting de glifos;
não há igualdade integral de pixels/avanços horizontais com Agg. O solver e
alguns detalhes de rasterização/posicionamento ainda diferem. Posições explícitas
de textos não ganham uma garantia geral de ausência de colisão.

## Marcadores e legendas

Legendas medem a caixa real de cada rótulo e do título, incluindo várias linhas
e mudanças individuais de fonte. A escala também mede suas legendas, mantém
margens verticais de 0,4 tamanho de fonte e continua reduzindo as graduações
quando a largura não permite números separados. No modo compacto não há uma
linha vazia para a unidade. Python e o viewer HTML usam o mesmo cálculo.

O exemplo `components.py` escolhe fundos brancos explícitos para as caixas de
legenda/escala; o default de legenda continua herdando a cor dos Axes, como
Matplotlib. “Manaus” usa `halo='white', halo_width=2` em vez de fundo retangular.

As dimensões de colorbar foram medidas em 16 configurações: quatro posições,
`shrink=1`/`0.75` e layout manual/constrained. No layout manual as dimensões
coincidem numericamente; nos casos constrained registrados diferem menos de
um pixel a 100 dpi. Isso não garante igualdade de posição ou de outros layouts.
Veja [medidas diretas](colorbar-size-reference.json) e
[probe de desenvolvimento](../tools/inspect_colorbar_sizes.py).
Para uma barra menor, use `fig.colorbar(points, ax=ax, shrink=.75)`; `aspect`
controla a proporção comprimento/espessura e `fraction` limita o espaço reservado.

`D` é um losango simétrico; `d` é o losango estreito. A geometria da estrela
também foi ajustada, e `+`/`x` respeitam markeredgecolor/markeredgewidth sem
espessura mínima adicional. Os mesmos desenhos são usados nos dados e na legenda.
Onze marcadores têm limites comparados aos paths da referência.

Ao recriar a legenda depois de ocultar uma linha, seu símbolo nasce oculto,
mas o texto continua presente, como na referência selecionada. Alterar a
visibilidade da linha depois de criar a legenda não muda essa cópia. Os estilos
de cor/traço dos handles ainda seguem a implementação existente de atualização
ao desenhar; não são uma cópia completa do sistema Legend/handlers Matplotlib.

## Notação científica e offset

`ScalarFormatter` escolhe precisão comum, escala científica e um offset aditivo.
Por exemplo, 100000, 100002, 100004 viram 0, 2, 4 com `+1e5` na borda.
O default de transição científica é `(-5, 6)`, e offset automático exige economia
de dígitos segundo `axes.formatter.offset_threshold` (default 4).

```python
from azimlib.ticker import ScalarFormatter, EngFormatter

ax.ticklabel_format(axis='x', style='plain', useOffset=False)
ax.ticklabel_format(axis='y', style='sci', scilimits=(-3, 4))
ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=-46))
ax.xaxis.get_offset_text().set(color='gray', fontsize=8, visible=True)

bar = fig.colorbar(points, ax=ax, orientation='horizontal')
bar.ax.ticklabel_format(style='sci', scilimits=(6, 6))
bar.ax.xaxis.get_offset_text().set_visible(False)
# Prefixos SI; 1500 -> 1.5 km:
bar.formatter = EngFormatter(unit='m')
```

Funciona também em barras verticais, nas quatro posições, compartilhadas e com
cax explícito. Clim altera os números/offsets; substituir o norm reseta tickers,
como no contrato já existente. Offset é TextArtist editável (fonte, cor,
alinhamento, rotação, visibilidade, in_layout) e participa de ownership/stale.
O texto é calculado novamente pelo formatter ao desenhar; set_text não fixa um
offset manual permanente. Setters do formatter invalidam o desenho; a
configuração em lote valida os eixos e opções antes de alterar qualquer um.

Também existem `set_scientific`, `set_powerlimits`, `set_useOffset`,
`set_useLocale`, seus getters de opções e `format_data`/`format_data_short`.
`axes.unicode_minus` controla o sinal. Locale usa o locale numérico ativo do
Python. EngFormatter aceita unit/places/sep, prefixos SI de quecto a quetta.

Limites explícitos: MathText/TeX e offsets de EngFormatter ainda não são
implementados e geram NotImplementedError. Formatar um ScalarFormatter solto
sem set_locs continua retornando um número simples, extensão histórica da API.
Os eixos geográficos permanecem longitude/latitude; notação não muda o CRS.
O HTML conserva a composição científica exportada, mas não recalcula offsets
científicos durante pan/zoom: esses ticks são ocultados ao navegar e restaurados
por Home, como os demais formatters não portáteis. Para recomposição completa,
use o viewer Tk.

## Exemplos e verificações

- [Traçados e textos versus Agg](../gallery/series-light-comparison.png).
- [Colorbars verticais](../gallery/numeric-vertical-comparison.png).
- [Colorbars horizontais](../gallery/numeric-horizontal-comparison.png).
- [Referência numérica, paths e 96 caixas de texto](numeric-formatting-reference.json).
- [Exemplo reproduzível](../examples/numeric_formatting.py).
- [Smoke Tk](../tools/smoke_numeric_tk.py), com dez verificações em widgets reais
  ocultos: offsets/editabilidade/clim/ticks, texto, marcadores, troca de formatter,
  navegação, exportação estática e fechamento. Não testa input físico/aparência
  nativa nem mede latência. CI inclui esse smoke, ainda sem execução remota.
- Relatórios [source](numeric-tk-validation.json) e
  [wheel instalado](numeric-tk-wheel-validation.json).

```bash
python examples/numeric_formatting.py
python tools/smoke_numeric_tk.py
# Apenas desenvolvimento com a referência instalada:
python tools/inspect_numeric_formatting.py
python tools/render_numeric_comparisons.py
```
