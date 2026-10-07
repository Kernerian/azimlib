# Eixos compartilhados e rótulos externos

Outputs under `gallery/` are local generated previews, not distributed assets.
For versioned current images, see the [0.3 gallery](gallery-0.3.md).

A implementação é própria. Matplotlib 3.11.2/Agg serve somente como referência
de desenvolvimento; não é importado pelo núcleo nem pelos exemplos.

```python
import azimlib as azl

fig, axs = azl.subplots(2, 2, sharex=True, sharey=True)
for ax in axs.flat:
    ax.map("brazil", fit=False)
axs[0, 0].set_extent((-58, -38, -34, -16))
axs[1, 1].set_xlim(-54, -42)  # todos os mapas recebem estes limites
fig.savefig("atlas.svg")
azl.show()                  # viewer Tk próprio, com vistas vinculadas
```

Os mapas mantêm camadas, projeções, cores, títulos, legendas, grades e
ornamentos independentes. Compartilhar longitude/latitude não adiciona grade,
legenda, colorbar, seta de norte ou minimapa. Esses componentes continuam opcionais.

## Grupos e ajuste dos dados

`azl.subplots`, `Figure.subplots` e `GridSpec.subplots` aceitam os mesmos modos:

| Valor | Grupo |
|---|---|
| `False`, `'none'` | cada mapa independente |
| `True`, `'all'` | todos os mapas |
| `'row'` | um grupo por linha |
| `'col'` | um grupo por coluna |

`subplot_mosaic(..., sharex=True, sharey=True)` aceita booleanos e inclui
mapas de grids filhos no mesmo grupo, como o Matplotlib. `subgridspec(...).subplots`
cria grupos locais ao grid filho; seu vizinho no grid pai permanece independente.

Também é possível usar `ax.sharex(other)`, `ax.sharey(other)`,
`fig.add_subplot(..., sharex=other)`, `fig.add_axes(..., sharey=other)` ou
`azimlib.pyplot.subplot(..., sharex=other)`. A criação copia os limites e a
flag de autoescala do eixo indicado. Não há operação pública para desfazer
o vínculo ou trocar o destino de um eixo já compartilhado.

`get_shared_x_axes()` e `get_shared_y_axes()` retornam uma consulta somente
leitura: `joined(a, b)` e `get_siblings(ax)`.

`set_xlim`, `set_ylim`, `set_extent`, pan e zoom Python/Tk propagam as dimensões
compartilhadas. A autoescala considera a união dos dados daquele grupo, mantendo
a outra dimensão independente. `relim()` continua recalculando apenas os dados
locais; `autoscale_view()` usa esses limites na união. Os dados de fundo com
`fit=False` continuam excluídos. Margens são locais; o eixo que solicita o ajuste
aplica suas margens ao intervalo comum, sujeito aos limites geográficos.

Como no Matplotlib, `set_autoscalex_on`/`set_autoscaley_on` editam a flag local.
`set_xlim(..., auto=False)` desliga a autoescala no grupo; `auto=None` preserva
as flags individuais. `emit=False` evita propagação e callbacks, permitindo
uma vista local temporariamente diferente. A navegação guarda/restaura vistas
e flags individuais sem sobrescrever entradas posteriores do histórico.

`ax.callbacks.connect('xlim_changed', func)` e `'ylim_changed'` recebem o
MapAxes alterado. A alteração do grupo é confirmada antes dessas notificações;
`callbacks.disconnect(cid)` remove a conexão. Erros de limites não propagam.

## Tickers compartilhados, estilo local

Locators e formatters maiores/menores são os mesmos objetos dentro do grupo.
Editar um deles ou chamar `set_xticks`/`set_yticks` atualiza os demais eixos.
Os tickers automáticos usam a área nominal do eixo ao qual estão anexados,
com proporção cartográfica, para evitar depender da ordem de desenho.

A fonte, rotação, cor e visibilidade dos textos continuam locais. Por exemplo:

```python
axs[1, 1].set_xticks([-54, -50, -46, -42])  # posições compartilhadas
axs[0, 0].tick_params(axis="x", labelbottom=True, labelcolor="red")
```

Não use um mesmo ticker em eixos independentes. Reatribuir o objeto a um
irmão do grupo é permitido. `clear()` conserva o vínculo; remover um MapAxes
o retira dos grupos e mantém os tickers dos mapas restantes operacionais.
O contexto copiado para um overview não participa do grupo do mapa principal.

## `label_outer()`

Ao compartilhar x com `'all'`/`'col'`, os ticks mantêm os rótulos de baixo
somente na última linha; ao compartilhar y com `'all'`/`'row'`, os rótulos
da esquerda ficam na primeira coluna. Ticks internos continuam visíveis.

`ax.label_outer()` aplica essa regra explicitamente às duas dimensões, inclusive
sem compartilhar eixos. `remove_inner_ticks=True` oculta também os ticks internos,
maiores e menores. Os rótulos superiores/laterais respeitam a primeira linha/
última coluna quando ativados com `tick_params`. Os títulos dos eixos x/y
atualmente têm posição fixa embaixo/à esquerda. `label_outer()` limpa os títulos
internos dessas posições; `tick_params(labelbottom=True)` pode reativar rótulos.

Grids aninhados seguem o SubplotSpec **local**, como na referência: o primeiro
mapa de um grupo filho pode exibir latitude mesmo com um mapa vizinho no pai.
Eixos criados por `add_axes` sem SubplotSpec não são alterados por `label_outer`.

## Exemplo, validação e limites

[shared_axes.py](../examples/shared_axes.py) produz antes (`gallery/shared-axes-before.png`, generated locally)
e depois (`gallery/shared-axes-after.png`, generated locally) em PNG/SVG: político, hidrografia,
coroplético e rotas com uma vista comum e colorbar adicionada explicitamente.
Os valores regionais e a rota são demonstrativos. A
comparação lado a lado (`gallery/shared-axes-reference.png`, generated locally) usa os mesmos
dados, limites, ticks, DPI e estilos em Agg/Azimlib.

O oracle `shared-axes-reference.json` registra 36 combinações de grupos e
rótulos, união dos dados, flags e um mosaico aninhado de Matplotlib 3.11.2.
As regressões também cobrem remoção do eixo principal, figuras distintas,
overview isolado, tamanhos diferentes, redraw repetido e histórico.

O vínculo funciona em Python e no modelo usado pelo viewer Tk. O teste GUI
real continua pendente: este ambiente não tem `init.tcl` funcional. O HTML
portátil sincroniza grupos em Mercator/equiretangular contínuas, preservando
aspecto e histórico da Figure; não recompõe toda a cena Python. Veja
[navegação portátil](portable-navigation.md) e seus exemplos interativos.
O exemplo shared_axes.py original continua exportando somente PNG/SVG.

Latitude/longitude permanecem em graus, com intervalos crescentes dentro dos
limites terrestres; não há inversão de eixos, escalas cartesianas arbitrárias,
grafo de transformações ou unidades compartilhadas completo. Compartilhar
eixos de colorbar com mapas é rejeitado. A compatibilidade e a igualdade visual
com Matplotlib continuam parciais.
