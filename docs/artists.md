# Edição e ciclo de vida dos Artists

Auditoria de validação antes da edição, representações numéricas/tracejados
próprios e integração Tk/exportação: [contratos e evidências](artist-validation.md).

Figure, MapAxes, Layer, TextArtist, Spine, legenda, frame e componentes
cartográficos compartilham `azimlib.artist.Artist`. Esta base é própria;
Matplotlib participa somente dos scripts de comparação no desenvolvimento.

```python
import azimlib as azl

fig, ax = azl.subplots()
ax.set_extent((-54, -43, -27, -19))
line, = ax.plot([-52, -48, -46.63], [-25, -23, -23.55], 'o--')
title = ax.set_title('Mapa inicial')

title.set_text('Mapa editado')
azl.setp(line, color='red', linewidth=1.5)
line.set_data([-52, -50, -46.63], [-25, -24, -23.55])
print(azl.getp(line, 'color'))
fig.canvas.draw_idle()
fig.savefig('mapa.svg')
```

## Propriedades e visibilidade

`artist.set(...)`, `setp(...)` e os setters existentes editam os mesmos
objetos que a composição utiliza. `getp(artist)`/`artist.properties()` retornam
um dicionário de propriedades editáveis implementadas. `setp` aceita também
listas aninhadas de artistas e pares nome/valor posicionais. A consulta
impressa de opções sem argumentos do setp de Matplotlib não foi implementada.

`set_visible(False)` oculta; `set_in_layout(False)` exclui das medições de
layout sem ocultar; `remove()` retira da composição. As APIs não acrescentam
grade, minimapa, legenda ou outros ornamentos automaticamente. Remoção e
`ax.clear()` desconectam os Artists antigos da figura: editar um handle
removido não solicita atualização da figura anterior.

Textos internos de legenda/ticks/colorbar não oferecem remoção individual;
use `set_visible(False)`. `remove()` informa `NotImplementedError`, como no
contrato de texto de entrada registrado diretamente na referência. Substituição
de componentes locais e descarte de ticks desconectam handles antigos; veja
[regras, exemplos e diferenças explícitas](component-lifecycle.md).

`ax.set_title`, `set_xlabel`, `set_ylabel` e `fig.suptitle` reutilizam seu
TextArtist, preservando propriedades anteriores não sobrescritas. A legenda
também mantém o mesmo handle de frame. `set_alpha(None)` de Layer remove a
opacidade explícita e retorna ao padrão de renderização.

Linhas permitem data=(x,y) ou xdata/ydata no mesmo set/setp que marcadores,
traços e visibilidade; textos/annotations aceitam text com seu estilo no lote.
Contornos têm handles próprios com widths/styles por nível e clabel retorna
uma lista de rótulos individuais editáveis. Veja [linhas e contornos](lines-contours.md).

Textos do mapa retornam MapText com posição/x/y editáveis; annotations permitem
editar destino xy e posição xyann/anncoords separadamente. Rótulos de legenda
e colorbar validam estilo/posição antes de gravar o lote. Veja
[edição de textos](text-edits.md), incluindo o contrato de offset points e a
diferença preservada dos offsets antigos em pixels.

`get_children()` lista filhos diretos; `findobj()` percorre o grafo sem
duplicatas, incluindo componentes ocultos. Aceita uma classe ou predicado:

```python
from azimlib.components import TextArtist
for text in fig.findobj(TextArtist):
    text.set_fontsize(9)
assert title.get_figure() is fig
```

## Atualização e callbacks

Uma edição marca o Artist, seu MapAxes e a Figure como `stale=True`.
Limpar o estado de um filho não limpa seu pai. `canvas.draw()` confirma uma
composição bem-sucedida e limpa os estados antes de emitir `draw_event`.
Se o desenho falhar ou um callback editar a figura depois dele, ela continua
pendente. Chamadas recursivas a draw durante draw_event são protegidas.

`to_scene()` e `savefig()` não confirmam o estado da janela: medição, exportação
e viewer permanecem separados. Esta regra de exportação não é uma reprodução
literal do estado interno de todos os backends do Matplotlib.

```python
cid = line.add_callback(lambda artist: print(artist.get_color()))
line.set(color='blue', linewidth=1.2)
line.remove_callback(cid)
```

O callback recebe o Artist depois da edição. Setters aninhados em uma chamada
`set()` do mesmo objeto são agrupados em uma notificação. A contagem exata
de notificações de cada setter do Matplotlib não é reproduzida. `pchanged()`
emite uma notificação explícita; `stale_callback(artist, True)` pode observar
a invalidação. Callbacks que levantam exceções as propagam ao chamador.

`ScalarMappable.callbacks.connect('changed', callback)` observa alterações
por `set_array`, `set_cmap`, `set_norm`, `set_clim` e `autoscale`. Colorbars se
inscrevem neste sinal: preservam locators customizados quando só clim muda e
reinicializam ticks quando norm é substituído. Remover a barra ou trocar seu
mappable desconecta a inscrição antiga. Atribuição direta a `norm.vmin`,
`norm.vmax`, `norm.clip` e `TwoSlopeNorm.vcenter` também notifica todos os
mappables associados. Dicionários internos, arrays e Colormap ainda exigem
setters ou changed(). Veja [normalização e limites](norm-limits.md).

## Modo interativo

O padrão é `ioff()`. Edições invalidam a figura e o redesenho explícito usa
`fig.canvas.draw_idle()`. Com o viewer Tk aberto, `ion()` agenda o redesenho
no event loop; várias solicitações pendentes são agrupadas pelo viewer.

```python
fig.show(block=False)  # Desktop Tk, depende do extra gui.
with azl.ion():
    line.set_color('red')
    title.set_text('Atualizado')
fig.canvas.flush_events()
```

`ion`, `ioff` e `isinteractive` existem no root e em pyplot. Os dois primeiros
também funcionam como context managers, restaurando o modo anterior. Sem
janela, draw_idle compõe a cena imediatamente. ion não abre janelas por si
só; `show()` continua explícito. O HTML é uma cena exportada e não recebe
edições posteriores do processo Python.

## Edição de dados e limites atuais

`get_data`/`set_data`, `get_xdata`/`set_xdata` e `get_ydata`/`set_ydata` editam
uma série geográfica simples criada por `plot` ou uma LineString única.
As entradas originais continuam imutáveis; consultas devolvem cópias. Uma
série pode ficar vazia ou conter um único ponto. A edição não muda a vista:
use `relim()` seguido de `autoscale_view()` nos eixos automáticos, ou defina
limites manuais com `set_extent`, `set_xlim`/`set_ylim`. Margens e estados de
autoescala têm controles próprios. ScatterCollection permite set_offsets/set_sizes
e edição coordenada de posições/array via setp; veja [coleções de pontos](scatter.md).
MeshCollection, ScalarImage e VectorCollection também permitem editar seus
dados por setters próprios, sem recriar handles. Veja [campos 2D](field-editing.md).

Esta entrega consolida um protocolo comum, não toda a hierarquia Line2D,
Patch, Collection, Transform, picking, blitting ou animação do Matplotlib.
Setters de Layer/Text validam estilos antes de alterar controles; não há
transação com rollback geral para lotes entre vários Artists. Consulte
[pendências](pending.md) e o [exemplo antes/depois](../examples/artists.py).

Dimensões/DPI públicos e títulos laterais independentes são descritos em
[integração de composição](sizing-composition.md).

Múltiplos grupos/matrizes, ciclos e defaults de legenda em contextos foram
consolidados no [lote de séries e estilos](series-styles.md).
