# GridSpec, proporções e painéis com spans

`GridSpec` próprio separa a alocação das células da projeção/renderização de
cada mapa. `SubplotSpec` descreve um retângulo de células, com a mesma forma
de chamada familiar de Matplotlib:

```python
import azimlib as azl

fig = azl.figure(figsize=(12, 8), layout="constrained")
gs = fig.add_gridspec(2, 3, width_ratios=[2.3, 1, 1])

brasil = fig.add_subplot(gs[:, 0], projection="mercator")
minas = fig.add_subplot(gs[0, 1:], projection="mercator")
sao_paulo = fig.add_subplot(gs[1, 1:], projection="mercator")

brasil.map("brazil")
minas.state("MG")
sao_paulo.state("SP")
fig.suptitle("Atlas regional")
fig.savefig("atlas.png", dpi=150)
azl.show()
```

As linhas são contadas de cima para baixo; colunas, da esquerda para a direita.
Índices são zero-based e aceitam valores negativos. `gs[0]` é a primeira célula
na ordem por linhas; `gs[-1]` é a última. `gs[:, 0]` ocupa toda a primeira
coluna, `gs[0, :]` ocupa toda a primeira linha. `gs[1:, 1:]` seleciona um bloco.
O fim de uma slice é exclusivo. A seleção cria um SubplotSpec, sem criar Axes.

Slices planas, como `gs[2:5]`, usam o retângulo definido pelas células inicial
e final, seguindo a referência. Esse retângulo pode conter células fora da
sequência plana. Para intenção clara, prefira `gs[rows, columns]`.

Também funcionam `fig.add_subplot(231)`, `fig.add_subplot(2, 3, 4)` e
`fig.add_subplot(2, 3, (2, 6))`: índices numéricos são **one-based**; o par
seleciona o retângulo entre as duas células. Chamadas numéricas da mesma forma
de grid reutilizam seu GridSpec; cada chamada cria um novo Axes.

## Proporções e espaços

```python
fig, axs = azl.subplots(
    2, 2, width_ratios=[2, 1], height_ratios=[1, 3],
    gridspec_kw={"wspace": 0.3, "hspace": 0.4},
)
# Alternativa: todos os parâmetros em gridspec_kw.
gs = axs[0, 0].get_gridspec()
```

Proporções são pesos relativos, copiados da entrada: `[2,1]` aloca à primeira
coluna duas vezes a largura útil da segunda. `width_ratios` tem um valor por
coluna; `height_ratios`, por linha. A área de um span inclui os espaços internos
entre suas células. Não corresponde necessariamente ao tamanho visível do mapa:
a proporção geográfica pode deixar espaço em branco no retângulo alocado.

`left`, `right`, `bottom` e `top` usam frações da Figure. `wspace`/`hspace`
usam frações da **largura/altura média das células**, independentemente dos pesos.
Opções locais têm precedência sobre `fig.subplots_adjust(...)`.
Quando não há opção local, o grid herda os parâmetros da Figure.

```python
fig.subplots_adjust(left=0.15, right=0.92, wspace=0.25)
gs.update(left=0.2, wspace=0.35)
gs.update(left=None)  # Volta a herdar o parâmetro da Figure.

gs.set_width_ratios([1, 2])
gs.set_height_ratios([2, 1])
gs.update()  # Aplica os novos pesos às posições em layout manual.
```

Como na referência, setters de proporção não reposicionam imediatamente Axes
em layout manual. `gs.update()` aplica as proporções atuais. Engines automáticos
leem esses pesos no próximo desenho. Valores inválidos são rejeitados antes de
alterar proporções, parâmetros ou posições.

## Layout e componentes

Tight/constrained próprios medem títulos, ticks, labels, legendas e colorbars
considerando os limites externos de cada span. Reservas de margem/espaçamento
são conservadoras; não são o solver do Matplotlib nem garantem pixels iguais.
Opções locais de margem limitam a área disponível ao solver. Espaços locais
são mínimos: decorações podem exigir separação maior.

Colorbar compartilhada funciona sobre a união dos mapas, incluindo spans:

```python
bar = fig.colorbar(layer, ax=[brasil, minas, sao_paulo], orientation="horizontal")
```

Também é possível reservar uma célula/span para `cax=fig.add_subplot(gs[...])`.
O retângulo desse cax continua explícito e não é movido pelo solver automático.
Para um atlas com cax reservado, use layout manual ou reserve uma área externa
ao rect do solver; ele ainda não evita esse cax como um obstáculo independente.
`add_axes()` também preserva seu retângulo manual.

`get_subplotspec()` retorna a seleção de um Axes; `get_gridspec()` retorna seu
grid. Em Axes manuais os dois retornam None. `spec.get_position(fig).bounds`
retorna a alocação nominal pelas margens/espaços, antes do solver automático
e da correção de aspecto do mapa. Não mede o viewport renderizado.
`gs.get_grid_positions(fig)` retorna tuplas de bottoms/tops/lefts/rights.
`gs.get_subplot_params(fig)` retorna uma cópia com acesso por chave ou atributo.

Os componentes continuam opcionais. GridSpec não acrescenta grade, legenda,
barra de escala, colorbar, minimapa, seta de norte ou rosa dos ventos.

## Escopo e diferenças deliberadas

- O solver automático suporta **uma hierarquia com um GridSpec raiz** por Figure, com spans e pesos.
  Grids distintos em layout manual funcionam. Quando há múltiplos grids ativos
  em layout automático, avisa e preserva todas as posições anteriores.
- `subplot_mosaic` e subgridspec aninhados estão disponíveis; veja
  [hierarquias](nested-layout.md). Ainda não há SubFigure ou compressed layout.
- `GridSpec.subplots(sharex='col', sharey='row')` e vínculos em mosaicos também
  estão disponíveis; consulte [eixos compartilhados](shared-axes.md).
- Slices só aceitam `step=1`. O Matplotlib instalado ignora alguns passos nas
  seleções; aqui passos não contíguos são rejeitados explicitamente.
- Pesos devem ser positivos e finitos; não se usam pesos zero para ocultar células.
- Um GridSpec pertence a uma Figure. `GridSpec(2, 2)` sem Figure é vinculado
  quando seu primeiro Axes é criado; reutilizá-lo em outra Figure é rejeitado.
- Seleções sobrepostas são permitidas, como Axes sobrepostos manuais. O solver
  não decide automaticamente ocultar ou remover um deles.
- HTML é uma cena exportada: não recalcula esse solver ao navegar.

[Exemplo completo](../examples/gridspec_atlas.py) e
[atlas renderizado](../gallery/gridspec-atlas.png).
`tools/inspect_gridspec.py` registra 24 seleções, seis estados de edição e três
seleções numéricas do Matplotlib 3.11.2/Agg em `gridspec-reference.json`.
Os testes comparam a alocação manual em frações de Figure; não exigem
Matplotlib instalado. O núcleo continua sem backend cartográfico externo.
