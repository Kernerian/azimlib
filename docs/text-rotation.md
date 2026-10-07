# Rotação e alinhamento de textos

Outputs under `gallery/` are local generated previews, not distributed assets.
For versioned current images, see the [0.3 gallery](gallery-0.3.md).

O alinhamento padrão usa a caixa completa **depois da rotação**, seguindo a
referência instalada Matplotlib 3.11.2. `rotation_mode='anchor'` alinha antes de
girar. `xtick` e `ytick` ajustam o alinhamento conforme o ângulo, como os modos
homônimos da referência; eles são opcionais, não o padrão dos ticks.

```python
import azimlib as azl

fig, ax = azl.subplots(layout='constrained')
ax.map('brazil')
ax.tick_params(labelrotation=35)  # default: caixa alinhada após girar
ax.set_xlabel('Longitude', labelpad=4)
ax.set_ylabel('Latitude', labelpad=4)  # vertical, anchor por padrão
ax.set_title('Brasil\nDivisões territoriais')

text = ax.text(-48, -15, 'Região', rotation=35, ha='center', va='top')
text.set_rotation_mode('anchor')
bar = fig.colorbar(azl.cm.ScalarMappable(azl.colors.Normalize(0, 100)), ax=ax)
bar.ax.tick_params(labelrotation=35, labelrotation_mode='ytick')
fig.savefig('mapa.svg')
```

`Text` de mapa, annotation, títulos, nomes dos eixos e textos da Figure usam as
mesmas regras próprias. `set_rotation()` aceita números, `'vertical'` e
`'horizontal'`; `set_rotation_mode()` e os getters permitem editar o modo.
`tick_params(labelrotation_mode=...)` atua nos ticks major/minor selecionados,
incluindo colorbars. PNG, SVG, Tk e ticks regenerados no HTML usam a mesma
convenção de ângulos. Nenhum caminho importa Matplotlib no runtime.

Um texto multilinha conserva uma caixa retangular única para layout, mesmo
quando suas linhas têm comprimentos diferentes. Nomes dos eixos reservam o
padding a partir das caixas dos ticks rotacionados; títulos automáticos
consideram as decorações que ultrapassam o topo. O layout não muda os valores
ou a quantidade de ticks fixados pelo usuário. Fontes grandes em painéis
pequenos ainda exigem aumentar a figura ou escolher menos ticks, como na
referência. Annotations/textos livres não recebem um solver universal de colisões.

## Verificação direta

- Comparação visual (`gallery/text-rotation-comparison.png`, generated locally): mesmos dados,
  posições, fontes e estilos em 0°, 35°, −35° e 90°; Azimlib/Pillow e Matplotlib/Agg.
- [Referência numérica](text-rotation-reference.json): 768 combinações de quatro
  modos, oito ângulos, três alinhamentos horizontais, quatro verticais e uma/duas
  linhas. A maior diferença de caixa é 1,43 pixel lógico a 100 DPI; a tolerância
  de fonte é 1,5 pixel, pois Agg arredonda/hinta avanços e o núcleo usa métricas
  fracionárias. Isso não declara identidade de pixels.
- `tests/test_text_rotation.py`: rejeição de modos inválidos antes da edição,
  ancoragem, escala e 1.536 comparações de planos Python/JavaScript em dois DPIs.
  O teste JavaScript precisa de Node no ambiente de desenvolvimento.

Reprodução: `python tools/inspect_text_rotation.py` e
`python tools/compare_text_rotation.py` no ambiente de referência com Matplotlib.
MathText, TeX e shaping complexo permanecem fora deste corte.
