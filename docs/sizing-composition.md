# Dimensões, títulos e integração de composição

Outputs under `gallery/` are local generated previews, not distributed assets.
For versioned current images, see the [0.3 gallery](gallery-0.3.md).

```python
import azimlib as azl

fig, ax = azl.subplots(figsize=(6.4, 4.8), layout='constrained')
ax.map('brazil')
ax.set_title('Brasil', loc='left', pad=8)
ax.set_title('Mapa político', loc='center')
right = ax.set_title('2026', loc='right')
right.set_visible(False)
fig.set_size_inches(8, 6)
fig.set_dpi(150)
fig.savefig('brasil.png', dpi=200)  # Não muda o DPI da Figure/viewer.
azl.show()
```

## Contratos públicos

`get_size_inches()` devolve uma tupla independente. `get_figwidth()`,
`get_figheight()` e `get_dpi()` consultam o estado. `set_size_inches(w, h)`
ou `set_size_inches((w, h))`, `set_figwidth()`, `set_figheight()` e `set_dpi()`
retornam `None`, validam números finitos positivos antes de alterar o estado
e participam de stale/callbacks/`setp`. Mudar DPI preserva as dimensões em
polegadas. Fontes, linhas e padding continuam expressos em pontos físicos.

Com viewer Tk aberto, `forward=True` ajusta o canvas e agenda redraw mesmo
em modo não interativo. `forward=False` mantém a solicitação de tamanho da
janela; `fig.canvas.draw()` renderiza explicitamente as novas dimensões.
Um viewer fechado não recebe resize. Atributos diretos antigos continuam
disponíveis; use os setters para notificação. O DPI de exportação PNG é
temporário; o SVG mantém o contrato atual de Scene/viewBox, sem prometer todas
as regras de unidades físicas do Matplotlib.

Há três títulos independentes, `loc='left'`, `'center'` e `'right'`.
`get_title(loc)` consulta cada slot. Repetir `set_title()` no mesmo slot
preserva seu handle; visibilidade, remoção e `clear()` são funcionais.
`pad` usa pontos e admite valores negativos finitos. `fontdict` é aceito,
com kwargs tendo precedência. `rcParams['axes.titlelocation']` e
`rcParams['axes.titlepad']` definem os padrões. O anchor acompanha `loc`;
`ha` modifica o alinhamento do texto naquele anchor. O padrão vertical é
baseline. Não existe redução automática de fonte para encaixar três títulos:
o exemplo aninhado usa fonte explicitamente menor nos mapas pequenos.

A [referência registrada](sizing-titles-reference.json) compara seis operações
de dimensões e os três títulos com Matplotlib 3.11.2/Agg. Os estados suportados
coincidem. Diferenças: tupla em vez de ndarray, dimensões zero rejeitadas,
e `y`/transforms de título fora deste contrato. Não há equivalência completa
com o sistema de transforms ou SubFigure da referência.

## Composição e exemplos

A [matriz registrada](composition-matrix-reference.json) contém 54 configurações:
mapa único, atlas e GridSpecs aninhados × tight/constrained × três tamanhos
por tipo × 100/150/200 DPI. Os 54 casos Azimlib completaram sem warnings ou
primitivas medidas fora da Figure. As dimensões lógicas são estáveis entre DPIs.
Também há regressões de recuperação após layout pequeno inviável, componentes
vizinhos e preservação de Axes/cax posicionados manualmente.

Na referência, 45 casos completaram: 18 emitiram warning de incompatibilidade
com tight layout, e nove casos aninhados/constrained com colorbar compartilhada
entre GridSpecs distintos falharam com IndexError. São resultados deste roteiro
e desta versão, não uma conclusão geral sobre Matplotlib. Os bounds são medidos
por primitivas próprias e tight bboxes nativos, respectivamente; solvers e
ornamentos diferem. A Azimlib adiciona escala/norte explicitamente; o núcleo
Matplotlib não fornece equivalentes diretos. Não se declara igualdade de pixels.

O teste usa polígonos e valores sintéticos. A [galeria](../examples/composition_matrix.py)
usa divisões reais Natural Earth embarcadas, com valores de estações sintéticos:
mapa (`gallery/composition-single.png`, generated locally), atlas (`gallery/composition-atlas.png`, generated locally)
e aninhado (`gallery/composition-nested.png`, generated locally). PNG/SVG são estáticos; HTML é
separado. Compare mapa (`gallery/composition-single-comparison.png`, generated locally) e
atlas (`gallery/composition-atlas-comparison.png`, generated locally) lado a lado com Agg.
Os layouts permanecem diferentes; textos livres e obstáculos posicionados
explicitamente não ganham uma garantia universal de ausência de colisão.

## Primeiro desenho e Tk

`show()` transfere callbacks e registra canvas/viewer antes do primeiro draw.
Um callback de `draw_event` já observa o estado pronto. Falha nesse callback
fecha/libera a janela, restaura o canvas/registro anteriores e permite nova
tentativa; o callback também pode fechar sua janela sem acesso posterior a
widgets destruídos. São regras da implementação própria.

O [smoke](../tools/smoke_composition_tk.py) cobre 14 cenários em Tk real oculto:
primeiro draw, edições agrupadas, resize, DPI, exportação temporária,
`forward=False`, recuperação de erro e fechamento em callback.
Relatórios: [source](composition-tk-validation.json) e
[wheel instalado](composition-tk-wheel-validation.json).
São eventos/edições programáticos; não medem aparência, input físico ou latência.
Os 17 testes novos somam 101 subtests. CI remota, conferência de janela nativa
e composição com bases densas continuam pendentes para a [0.2.0](release-0.2.md).

```bash
python examples/composition_matrix.py
python tools/smoke_composition_tk.py
# Somente desenvolvimento, com Matplotlib instalado:
python tools/inspect_sizing_titles.py
python tools/compare_composition_matrix.py
python tools/render_composition_comparisons.py
```
