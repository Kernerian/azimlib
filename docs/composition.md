# Legendas, colorbars e vários mapas

Os componentes são desenhados pelo núcleo próprio, em PNG, SVG e na janela Tk.
Matplotlib é usado somente pelas ferramentas de comparação de desenvolvimento.
Execute `python examples/composition.py` para reproduzir as três figuras.

## Legenda em várias colunas

```python
legend = ax.legend(
    [states, rivers, (route, cities)],
    ['Estados', 'Rios', 'Rota e cidades'],
    ncols=2, loc='upper center', bbox_to_anchor=(.5, -.08),
    title='Camadas', columnspacing=2,
)
legend.get_texts()[0].set_text('Divisões estaduais')
legend.get_title().set_color('navy')
legend.get_frame().set_alpha(.8)
legend.set_ncols(1)
legend.set_visible(False)
```

As entradas preenchem a primeira coluna antes de passar à seguinte. Cinco
entradas em duas colunas formam grupos de três e duas. `ncol` é aceito como
alias; `ncols` prevalece se ambos forem fornecidos. Um handle composto,
como `(route, cities)`, sobrepõe os símbolos em uma mesma amostra. Os estilos
dos handles permanecem vivos após a criação da legenda.

`loc` aceita os nomes e códigos 0–10 do Matplotlib, ou uma posição `(x, y)`.
O padrão é `best`, que escolhe entre dez posições considerando colisões com
geometrias, pontos, textos, annotations, norte e escala. É uma heurística
própria: não garante o mesmo resultado do Matplotlib em todas as cenas;
campos raster, vetores e labels automáticos ainda não entram nesse cálculo.
Use `loc` explícito para mapas densos ou para preservar uma composição fixa.

`bbox_to_anchor=(x, y)` define uma referência; `(x, y, width, height)` define
uma caixa. As frações usam os eixos do mapa, com origem inferior esquerda.
`bbox_transform='figure'` usa a figura inteira; esta opção é uma conveniência
Azimlib, não um objeto de transformação Matplotlib. `mode='expand'` distribui
as colunas na largura da caixa, sem comprimir o conteúdo abaixo da sua largura
mínima. Uma legenda fora dos eixos pode reservar espaço com os engines
`tight`/`constrained` próprios; veja [layout](layout.md). Sem engine automático,
reserve espaço com `fig.subplots_adjust(...)`.

O título é opcional. `ax.legend()` não adiciona a palavra “Legenda”.
`get_texts()` e `get_title()` retornam textos editáveis; `get_frame()` retorna
uma fachada editável. `set_visible()` e `remove()` afetam a legenda inteira.

## Colorbar compartilhada

```python
import azimlib.pyplot as plt
from azimlib import datasets
from azimlib.colors import Normalize

data = datasets.load('states', country='brazil')
values = list(range(len(data['features'])))
norm = Normalize(0, len(values) - 1)
fig, axs = plt.subplots(2, 2, figsize=(9, 8))
layers = []
for ax in axs.flat:
    layers.append(ax.choropleth(data, values, bins=None,
                               norm=norm, cmap='viridis'))
bar = fig.colorbar(layers[0], ax=axs, orientation='horizontal')
bar.set_label('Indicador')
bar.set_ticks([0, 10, 20])
fig.savefig('atlas.png')
```

`ax` pode ser um mapa, uma sequência ou o grid retornado por `subplots`.
A barra automática reserva espaço no retângulo que envolve todos os pais;
as proporções e os espaços relativos do grid são preservados. Os mapas
continuam usando aspecto cartográfico isotrópico, portanto podem ocupar uma
área menor que o espaço reservado. A composição é recalculada a cada desenho.
Ocultar ou remover a barra devolve o espaço aos mapas sem alterar suas
posições configuradas. É possível adicionar mais de uma barra compartilhada;
cada uma reserva seu espaço em ordem de criação.

Compartilhar `Normalize` explicitamente faz a alteração de limites em uma
camada afetar todas as que usam esse objeto. A barra representa **um** mappable:
alterar sua paleta não altera automaticamente a paleta de outras camadas.
Mantenha a mesma `norm` e a mesma `cmap` em todos os mapas comparáveis.

## Eixos explícitos — cax

```python
cax = fig.add_axes((.88, .18, .025, .60))
bar = fig.colorbar(layers[0], ax=axs, cax=cax)
assert bar.ax is cax
cax.set_yticks([0, 10, 20], labels=['Baixo', 'Médio', 'Alto'])
cax.tick_params(labelsize=9, colors='black')
cax.set_ylabel('Indicador', fontsize=10)
```

Com `cax`, o retângulo fornecido determina a posição e o tamanho: os pais não
perdem espaço e `fraction`, `shrink`, `aspect` e `pad` não dimensionam a barra.
Use `orientation='horizontal'`, ticks X e `set_xlabel` para uma barra horizontal.
O `cax` deve pertencer à figura e não conter camadas, insets ou outra colorbar.
Ele passa a representar a barra e sai da navegação geográfica; `bar.remove()`
também remove esse eixo da figura. Remoção repetida é segura.

Sem `cax`, `bar.ax` oferece uma fachada de ticks, rótulo e visibilidade; não
é um MapAxes completo. Locators/formatters como objetos já estão disponíveis
no [guia de ticks](ticks.md); ainda faltam handlers de legenda customizados,
transformações arbitrárias e grids aninhados. GridSpec raiz com spans já funciona;
veja [composição com spans](gridspec.md).
No HTML exportado, os componentes são fixos; edições Python exigem exportar
novamente. O backend Tk usa os objetos Python vivos.

## Verificação da referência

`tools/inspect_composition.py` usa Matplotlib/Agg no ambiente de referência e
registra `composition-reference.json`: ordem das colunas, escolha de `best`
em uma cena controlada, alocação de barras compartilhadas vertical/horizontal
e retângulo de `cax`. Os testes normais não exigem Matplotlib instalado.

Regras consultadas na documentação oficial:
[Axes.legend](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.legend.html)
e [Figure.colorbar](https://matplotlib.org/stable/api/_as_gen/matplotlib.figure.Figure.colorbar.html).
