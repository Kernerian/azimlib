# Normalização compartilhada e limites de vista

Normalize, ScalarMappable e os limites geográficos são implementações próprias.
O script de desenvolvimento `tools/inspect_norm_limits.py` usa Matplotlib
3.11.2/Agg como referência e gera [os casos comparados](norm-limits-reference.json).
Matplotlib não é dependência da biblioteca.

## Cores compartilhadas

```python
import azimlib as azl
from azimlib.colors import Normalize

fig, axes = azl.subplots(1, 2)
norm = Normalize(0, 100)
left = axes[0].scatter(lon=[-46.63], lat=[-23.55], c=[60], norm=norm)
right = axes[1].scatter(lon=[-43.17], lat=[-22.90], c=[90], norm=norm)
bar = fig.colorbar(left, ax=axes, orientation='horizontal')
norm.vmax = 200  # Atualiza as duas camadas e a barra.
fig.canvas.draw_idle()
fig.savefig('cores.svg')
```

As propriedades `vmin`, `vmax`, `clip` e `TwoSlopeNorm.vcenter` notificam seus
mappables. Reatribuir o mesmo valor não emite uma alteração. O sinal
`norm.callbacks.connect('changed', callback)` chama o callback sem argumentos;
o sinal correspondente do mappable passa o próprio mappable. A ligação usa
métodos fracos e desconecta a norm antiga ao substituí-la.

Alterar limites da mesma norm preserva locators e formatters customizados da
colorbar. Substituir a identidade da norm reinicializa seus ticks. Remover a
colorbar desconecta sua inscrição. Uma norm pode servir camadas de várias figuras.

`mappable.set_clim(low, high)` valida e altera o par antes de notificar, inclusive
quando ambos os novos limites ultrapassam o intervalo antigo. `autoscale()`
recalcula os dois limites pelos dados válidos; `autoscale_None()` preenche somente
os ausentes. Uma operação sobre dados válidos comunica o intervalo final, sem
publicar os limites intermediários. A atribuição isolada de vmin/vmax pode deixar
um intervalo temporariamente invertido; o mapeamento rejeita esse intervalo.
Prefira set_clim para substituir um par.

Limites explícitos NaN/infinito são rejeitados; valores não finitos nos dados são
ignorados. LogNorm usa dados positivos para autoescala. `norm.scaled()` indica
que ambos os limites estão definidos. Uma ScalarMappable independente sem dados
permite uma barra linear inicial 0–1. Os intervalos provisórios próprios de
LogNorm e TwoSlopeNorm são respectivamente 1–10 e center±1; não são promessas de
igualdade de todos os casos vazios do Matplotlib. Uma Layer sem dados numéricos
exige limites explícitos para criar uma colorbar.

Normalizações contínuas retornam floats: o extremo cortado `1.0` corresponde à
última cor da paleta. BoundaryNorm mantém seus índices inteiros discretos.
Mutações internas de arrays, dicionários ou Colormap não notificam: use setters
ou `mappable.changed()`. Reclassificação de quantis e regeneração de legendas
temáticas discretas ainda precisam de trabalho adicional.

## Dados e vista são controles distintos

```python
fig, ax = azl.subplots()
line, = ax.plot([-52, -48], [-25, -21], 'o--')
line.set_data([-54, -43], [-28, -18])
ax.relim()             # Recompõe os limites dos dados; conserva a vista atual.
ax.autoscale_view()    # Ajusta somente os eixos com autoescala habilitada.
ax.set_xlim(-55, -42)  # Fixa longitude; latitude pode continuar automática.
ax.autoscale(axis='x', tight=True)  # Reabilita X e remove sua margem.
```

Edição de dados não move a vista por si só. `set_extent` fixa ambos os eixos;
`set_xlim`/`set_ylim` fixam apenas o respectivo eixo, com `auto=False` por padrão.
`auto=True` reabilita e `auto=None` preserva o estado. Há getters/setters
`get_autoscalex_on`, `get_autoscaley_on` e `get_autoscale_on` e seus pares set.
`autoscale(enable=False)` desabilita; `enable=None` mantém os estados atuais.
Home/voltar/avançar restauram também os estados de autoescala da vista registrada.

`ax.margins()` consulta as margens sem invalidar a figura. O padrão é 5% por
eixo, configurável por `axes.xmargin`/`axes.ymargin`. `ax.margins(.1)` muda ambos;
`ax.margins(x=.1, y=-.1)` admite recorte com margens negativas maiores que -0.5.
Os limites manuais continuam fixos. As políticas explícitas de map/state são
preservadas. Sem dados novos, relim/autoscale_view conservam a vista.

`relim(visible_only=True)` exclui camadas ocultas. A recomposição inclui
geometrias, pontos de scatter, bordas de mesh e origens de vetores; ignora
texto, ornamentos, insets e camadas com `fit=False`. Assim, um mapa de fundo não
impede a autoescala de uma rota. A inclusão dessas coleções geográficas é uma
extensão própria: o relim do Matplotlib tem restrições para Collections.

## Limites desta implementação

Os limites são longitude/latitude em graus e ficam no domínio ±180°/±90°.
Um dado singular recebe expansão inicial de ±0.5° antes da margem, uma regra
geográfica própria. Não há ainda vistas invertidas ou que cruzam o antimeridiano.
`tight` controla a política de dados/margens disponível; sticky_edges,
round_numbers, shared axes e unidades extensíveis continuam pendentes.

Veja o [exemplo antes/depois](../examples/norm_limits.py), o
[ciclo de vida de Artists](artists.md) e as [pendências](pending.md). O HTML é
uma cena exportada: alterações posteriores no processo Python exigem nova exportação.
