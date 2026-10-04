# Teclado, mouse e atalhos no viewer Tk

O viewer interpreta os eventos com implementação própria. Matplotlib é apenas
referência de desenvolvimento; nenhum normalizador/backend dele é importado
em execução. O HTML portátil conserva seu sistema JavaScript e suas limitações;
os contratos abaixo se referem ao Tk.

## Eventos e propriedades

`fig.canvas.mpl_connect(nome, callback)` conecta uma função. O callback recebe
um objeto com `name`, `canvas`, `inaxes`, `x/y`, `xdata/ydata` e `guiEvent`.
Display usa pixels a partir do canto inferior esquerdo; `x/y` são inteiros,
mas a inversa geográfica usa a posição original, antes de truncar. Fora de
um mapa, `inaxes` e coordenadas geográficas são `None`.

| Canal | Propriedades e comportamento |
|---|---|
| `key_press_event`, `key_release_event` | `key` normalizado: `ctrl+s`, `P`, `enter`, `pageup`, Unicode; mapa sob o cursor |
| `button_press_event`, `button_release_event` | `button` em MouseButton, `modifiers`, `dblclick`; clique do meio também é informado |
| `motion_notify_event` | `buttons` frozenset dos botões atualmente pressionados; `button` é o último press ainda sem release |
| `scroll_event` | `step` fracionário, `button='up'/'down'`, `modifiers`; delta zero não navega |
| `figure_enter_event`, `figure_leave_event` | entrada/saída do canvas; sair limpa a mensagem de coordenadas |
| `axes_enter_event`, `axes_leave_event` | mudança de mapa durante motion; sair do anterior precede entrar no novo |
| `draw_event`, `resize_event`, `close_event` | cena desenhada, dimensão alterada e fechamento |

Mouse usa `modifiers` como frozenset de nomes: ctrl, alt, shift e, conforme
plataforma, cmd/super. Em teclado, os modificadores fazem parte de `key`; o
campo `modifiers` permanece vazio, como na referência. A tecla pressionada
também aparece em eventos de mouse até o release. Em axes_enter, o payload
é o motion atual, inclusive `event.name='motion_notify_event'`, como Matplotlib.
Em axes_leave, o payload informa o Axes anterior e a posição atual do cursor.

```python
from azimlib.backend_bases import MouseButton

def on_click(event):
    if event.inaxes is ax and event.button == MouseButton.LEFT:
        if 'ctrl' in event.modifiers:
            print(event.xdata, event.ydata)

cid = fig.canvas.mpl_connect('button_press_event', on_click)
# fig.canvas.mpl_disconnect(cid)
```

MouseButton possui LEFT=1, MIDDLE=2, RIGHT=3, BACK=8 e FORWARD=9 e continua
comparável com inteiros. Botões 2/3 e máscaras têm a conversão própria de Tk
em macOS. Botões extras só funcionam quando o sistema/Tk os entrega.
Isso não implementa as classes MouseEvent/KeyEvent/LocationEvent completas.

## Atalhos configuráveis

| rcParam | Default |
|---|---|
| `keymap.home` | h, r, home |
| `keymap.back` | left, c, backspace, MouseButton.BACK |
| `keymap.forward` | right, v, MouseButton.FORWARD |
| `keymap.pan` | p |
| `keymap.zoom` | o |
| `keymap.save` | s, ctrl+s |
| `keymap.fullscreen` | f, ctrl+f |
| `keymap.quit` | ctrl+w, cmd+w, q |
| `keymap.grid` | g |
| `keymap.grid_minor` | G |

Maiúsculas e modificadores são significativos: P e Ctrl+P não ativam pan por
padrão. Escape não fecha a janela por padrão. A grade maior, com g, percorre
desligada → X → X+Y → Y → desligada. G percorre o mesmo ciclo para as grades
maior+menor. Desligar uma grade maior desliga também sua menor. Atalhos de
grade só atuam sobre o mapa sob o cursor; a grade continua opcional/desligada
por padrão. +/- e roda são conveniências próprias de zoom, além da toolbar.

```python
import azimlib as azl

with azl.rc_context({'keymap.pan': ['ctrl+p'], 'keymap.save': []}):
    fig, ax = azl.subplots()
    ax.map('brazil')
    azl.show()
```

As configurações são lidas ao receber cada evento: mantenha o contexto ativo
durante o viewer. Listas são copiadas e validação de update é prospectiva;
`[]` desativa um atalho. O [exemplo interativo](../examples/viewer_events.py)
conecta clique com Ctrl a uma annotation e alterna legenda/escala/norte/rosa
individualmente, sem substituir os componentes uns pelos outros.

## Evidência e limites

[Contratos registrados](tk-input-reference.json) de Matplotlib 3.11.2/TkAgg:
60 teclas, 36 estados de máscaras, 15 botões, 10 transições, oito passos de
grade e dez keymaps. A execução usou Tk real oculto no Windows; as tabelas
Linux/macOS foram examinadas substituindo o identificador de plataforma
durante a chamada ao normalizador instalado. Isso não valida input nativo
nesses sistemas. O smoke próprio de doze cenários passou em Tk real oculto com
inputs sintéticos, também no wheel instalado sem Matplotlib/GIS. O exemplo
de componentes/Ctrl+clique passou nesse ambiente, incluindo exportação SVG.

Ainda faltam picking/selectors, hierarquia completa de classes de eventos,
mouse grab, foco em insets/colorbars, transições entre janelas diferentes,
política geral de exceções de callbacks e integração incremental. Existem
diferenças: eventos guardam o guiEvent depois da chamada; key_press é entregue
antes do atalho da toolbar; configurações duplicadas usam a prioridade local;
não há visibilidade individual de cada linha de tick para o caso misto de grid.
Atalhos de escalas logarítmicas, clipboard/help/quit_all não são implementados.
Conferência visual/input nativo e CI remota continuam pendentes. Veja
[validação desktop](viewer-validation.md); não se declara equivalência integral.
