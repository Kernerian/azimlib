# Rótulos globais e textos da Figure

Outputs under `gallery/` are local generated previews, not distributed assets.
For versioned current images, see the [0.3 gallery](gallery-0.3.md).

`suptitle`, `supxlabel` e `supylabel` pertencem à Figure e servem a todos os
mapas de um atlas. São opcionais e devolvem um Artist próprio editável:

```python
import azimlib as azl

fig, axes = azl.subplots(1, 2, figsize=(9, 6), layout="constrained")
for ax in axes.flat:
    ax.states(facecolor="white", edgecolor="black", linewidth=0.4)

title = fig.suptitle("Atlas regional")
xlabel = fig.supxlabel("Longitude")
ylabel = fig.supylabel("Latitude")
xlabel.set(text="Longitude geográfica", fontsize=13, color="#333333")
ylabel.set_visible(False)
fig.savefig("atlas.svg")
```

As chamadas seguintes reutilizam o mesmo handle, atualizam texto/posição e
reaplicam defaults de fonte, peso, alinhamento e rotação, como na referência
instalada. Outras propriedades já editadas, como cor/visibilidade, permanecem
até serem fornecidas novamente. `get_suptitle()`, `get_supxlabel()` e
`get_supylabel()` devolvem o texto ou `""` se não existir.

| Componente | Posição inicial `(x,y)` | Alinhamento | Rotação |
|---|---|---|---:|
| `fig.suptitle()` | `(0.5, 0.98)` | center/top | 0° |
| `fig.supxlabel()` | `(0.5, 0.01)` | center/bottom | 0° |
| `fig.supylabel()` | `(0.02, 0.5)` | left/center | 90° |

As coordenadas são frações da Figure, com Y para cima. Os defaults de fonte
usam `figure.titlesize/titleweight` e `figure.labelsize/labelweight` em
`rcParams`. O tamanho padrão `"large"` equivale a 1,2 vezes `font.size` (12 pt
com base de 10 pt). Tamanhos numéricos e nomes usuais são aceitos nestas
propriedades; isso não amplia automaticamente os contratos de todos os outros
componentes de texto.

## Edição, visibilidade e ownership

```python
title.set_position((0.5, 0.95))
title.set_x(0.45)
azl.setp(xlabel, text="Coordenada X", position=(0.5, 0.02), color="black")
xlabel.get_position()
xlabel.set_in_layout(False)  # desenha, mas não reserva margem
xlabel.set_visible(False)   # não desenha
xlabel.remove()             # remove o handle da Figure
```

Textos criados por `fig.text(x, y, ...)` também têm posição editável, setters
de alinhamento/rotação e `rotation_mode="default"/"anchor"`. Default alinha a
caixa após rotação; anchor gira o texto já alinhado ao redor da posição.
Os rótulos globais usam default. Métricas, shaping complexo e a baseline de
texto rotacionado ainda não são integralmente equivalentes ao Matplotlib.

Lotes de posição/estilo são validados antes de mudar o estado e notificam uma
vez com o resultado final. Edição invalida a Figure; `clear()` desanexa os
handles e limpa os três slots. `fig.text()` continua um texto livre, sem
reserva automática de espaço ou correção geral de colisões.

`azimlib.pyplot.suptitle()` e `figtext()` usam a Figure corrente. Como no
Matplotlib instalado, `supxlabel/supylabel` são métodos da Figure, sem
funções homônimas em pyplot.

## Regras de layout

- Sem engine: as posições e as margens são manuais.
- `fig.tight_layout()`: reserva as dimensões dos rótulos uma vez, sem mover os
  textos. O engine `layout="tight"` repete a medição a cada desenho.
- `layout="constrained"`: só posiciona/reserva os rótulos globais automáticos.
  Omitir Y em suptitle/supxlabel ou X em supylabel marca aquela borda como
  automática. Fornecer explicitamente a coordenada marca a posição como manual.
- Editar diretamente o handle não troca esse marcador. Para controlar a borda
  em constrained, chame novamente `fig.supxlabel(..., y=...)`, por exemplo.
- Ocultar, remover ou excluir do layout libera espaço no próximo cálculo.
- Grids simples e hierarquias com um grid raiz usam as mesmas reservas;
  colorbars/legendas continuam medidas junto aos mapas. Sem espaço, o solver
  avisa e restaura posições dos Axes, textos automáticos e subplotpars.

Não adiciona grid, norte, escala ou minimapa. A exportação HTML recebe o layout
composto; não executa esse solver Python ao navegar no browser.

## Exemplo e validação

O atlas (`gallery/figure-labels-atlas.png`, generated locally) combina os três rótulos globais,
dois mapas, ticks rotacionados, colorbar horizontal, legenda, escala e norte.
Seu [código](../examples/figure_labels.py) usa apenas Azimlib.

Comparações com Axes/layout independentes do Matplotlib:
tight (`gallery/figure-labels-tight-comparison.png`, generated locally),
constrained (`gallery/figure-labels-constrained-comparison.png`, generated locally) e
hierarquia (`gallery/figure-labels-nested-comparison.png`, generated locally). São exemplos com
os mesmos dados/tamanhos/estilos, não imagens iguais. Há diferenças de fontes,
reservas, aspecto e comprimento da colorbar; os solvers não são equivalentes.
O caso tight não tem colorbar; os casos constrained demonstram barras
compartilhadas, e na hierarquia a barra pertence somente ao grid filho.

[16 contratos](figure-labels-reference.json) foram registrados diretamente do
Matplotlib 3.11.2/Agg e comparados em testes sem importar Matplotlib. Doze novas
regressões incluem 24 combinações de layout/hierarquia/tamanho/DPI, edição,
visibilidade, remoção, falha atômica, exports SVG/HTML e exemplos PNG. O script de desenvolvimento
`tools/inspect_figure_labels.py` recria os contratos e as três comparações;
Matplotlib não integra o runtime.

Dimensões/DPI públicos e títulos laterais independentes são descritos em
[integração de composição](sizing-composition.md).
