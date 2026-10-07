# Edição de textos do mapa e annotations

Outputs under `gallery/` are local generated previews, not distributed assets.
For versioned current images, see the [0.3 gallery](gallery-0.3.md).

`ax.text()` devolve um `MapText` e `ax.annotate()` devolve uma `Annotation`
própria. Ambos continuam subclasses de Layer/Artist, com visibilidade,
remoção, callbacks, invalidação e estilo usados pela mesma composição.

```python
import azimlib as azl

fig, ax = azl.subplots()
ax.set_extent((-54, -42, -28, -16))
text = ax.text(-48, -22, "Local inicial")
text.set(position=(-46, -20), text="Local editado", color="red", ha="center")
text.set_x(-45)
text.set_y(-19)
print(text.get_position())
```

Posição significa longitude/latitude em graus com `transform="data"`, ou
frações do Axes com `transform="axes"`. `set_position`, `set_x/set_y` e os
respectivos getters respeitam esse sistema; não deslocam limites nem disparam
autoescala. `setp/getp` também aceitam essas propriedades. Latitude geográfica
é validada em [-90,90]; longitude segue o núcleo existente, inclusive valores
desenrolados. Posições fora do Axes podem ser cortadas pelo viewport.

Os handles oferecem `set/get_horizontalalignment`, `set/get_verticalalignment`
e aliases ha/va, fontfamily/fontstyle, size/weight. Texto de título, rótulo,
legenda e colorbar também recebe esses setters de estilo. A família suportada
é uma string; isso não reproduz FontProperties e sua lista de fallback. Fonte
em tamanho numérico e os limites de shaping existentes continuam válidos.
Rotação consultada é normalizada em [0,360), como na referência.

## Posição do texto e destino da annotation

```python
note = ax.annotate(
    "Destino", xy=(-48, -22), xytext=(18, 20),
    textcoords="offset points", color="#553377"
)
note.xy = (-44, -20)       # destino geográfico da seta
note.xyann = (-100, -26)  # posição do texto no sistema textcoords
note.set_position((-80, 12))
note.set_anncoords("offset points")
```

`get_position()`/`set_position()` editam o texto, preservando xy. `xy` é sempre
o destino lon/lat; `xyann` acompanha a posição do texto. `get_anncoords()` e
`set_anncoords()` consultam/trocam o sistema, sem converter numericamente os
valores existentes, como na referência.

| textcoords/anncoords | Unidades | Y positivo |
|---|---|---|
| `"data"` | graus lon/lat | norte |
| `"axes fraction"` ou alias anterior `"axes"` | frações do mapa | para cima |
| `"offset points"` | pontos físicos a partir de xy | para cima |
| `"offset pixels"` anterior | pixels lógicos a 100 DPI a partir de xy | para baixo |

`offset points` preserva a distância física ao variar DPI/projeção. O caminho
anterior `offset pixels` e seu default de `(20,-20)` foram mantidos para não
alterar exemplos existentes; **não são a semântica de offset pixels do
Matplotlib**. Use `offset points` para a convenção familiar de anotação.

O lote abaixo é uma conveniência adicional própria: xy, posição, sistema e
estilo são validados juntos antes de alterar o mesmo handle.

```python
note.set(
    xy=(-44, -20), position=(0.6, 0.8), anncoords="axes fraction",
    text="Novo destino", color="blue", fontsize=12
)
```

Recomposição de seta, texto, clipping e obstáculos de labels utiliza as
coordenadas editadas. `set_visible(False)` e `remove()` continuam funcionando;
editar um handle removido não invalida sua Figure antiga. Não cria um sistema
geral de Transforms, xycoords customizados, picking ou edição por arrastar.
Arrowprops/FancyArrowPatch ainda não estão implementados. O estilo de seta
próprio e seus limites continuam os anteriores. Camadas de texto agora oferecem
[rotation_mode](text-rotation.md), compartilhado com os demais textos.

## Títulos e rótulos de componentes

```python
legend = ax.legend(title="Pesquisa")
legend.set_title("Pesquisa atualizada", fontsize=11, color="black")
bar.set_label("Indicador atualizado", labelpad=6, loc="center", fontsize=11)
```

Estilo/alinhamento inválido não deixa o texto parcialmente modificado.
`Colorbar.set_label()` valida também labelpad/loc antes de gravar; o título da
legenda e seu dicionário, ou o rótulo da barra e sua posição, chegam coerentes
aos callbacks. Um lote válido notifica uma vez por handle editado; a contagem
exata de callbacks do Matplotlib não é reproduzida. Exceções em callbacks
ocorrem após o commit e não desfazem a edição, como no protocolo Artist existente.

## Exemplos e validação

O [exemplo](../examples/text_edits.py) exporta
antes (`gallery/component-text-edits-before.png`, generated locally) e
depois (`gallery/component-text-edits-after.png`, generated locally), incluindo mapa, texto,
annotation, legenda, escala e colorbar horizontal, sem Matplotlib.
Os comparativos antes (`gallery/text-edits-before-comparison.png`, generated locally) e
depois (`gallery/text-edits-after-comparison.png`, generated locally) usam Axes/layout
independentes no Matplotlib instalado e as mesmas coordenadas/estilos.
Fontes, clipping de texto, composição e setas apresentam diferenças; não há
igualdade de pixels ou implementação completa do sistema Text/Annotation.

[19 estados](text-edits-reference.json) foram registrados diretamente de
Matplotlib 3.11.2/Agg e verificados em testes sem importar a referência.
As regressões também verificam edição atômica, callbacks finais, ownership,
projeções/DPI, offsets, obstáculos e exportação própria.
`tools/inspect_text_edits.py` recria contratos/comparativos em desenvolvimento.
Nenhum renderizador ou classe do Matplotlib é usado no runtime.
