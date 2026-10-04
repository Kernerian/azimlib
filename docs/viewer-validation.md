# Validação do viewer Tk e do pacote instalado

O viewer continua próprio: Tk fornece widgets e Pillow o buffer de imagem;
geometria, projeção, composição e rasterização pertencem à Azimlib.
Matplotlib 3.11.2 foi utilizado somente na referência de desenvolvimento.

## Integração desktop executada

Em Windows 11, Python 3.14.4/Tk 8.6, os dois smokes executaram com janelas Tk
reais **ocultas**, widgets e event loop reais. Entradas sintéticas são chamadas
nos handlers registrados; não são movimentos físicos de mouse. Isso valida
integração funcional, não aparência da janela do SO. Veja o
[relatório local](viewer-tk-validation.json).
Os mesmos smokes também passaram no [wheel instalado](viewer-tk-wheel-validation.json),
em ambiente separado com Pillow e sem Matplotlib/GIS; importação do código
instalado foi conferida em modo isolado (`python -I`). O smoke do núcleo passou
em outro ambiente novo sem nenhuma dependência opcional.

O smoke inicial tinha nove cenários. Input ampliou para doze; buffer direto
acrescenta o décimo terceiro:

1. Toolbar, canvas, componentes opcionais e transferência dos callbacks.
2. Edições agrupadas em um redesenho, visibilidade e Scene em draw_event.
3. Registro da entrada de movimento e coordenadas do cursor.
4. Pan, eixos compartilhados e Home/Back/Forward.
5. Zoom retangular, remoção da seleção e passos fracionários da roda.
6. Recentrar pelo minimapa, foco e visibilidade do componente.
7. Registro de Configure, temporizador real e nova dimensão da cena.
8. Save da toolbar produz PNG/SVG estáticos; cancelar o diálogo não salva.
9. Fechar cancela tarefas, remove o viewer do registro e libera imagens.
10. Teclas normalizadas, keymaps editáveis e cancelamento de Ctrl+S.
11. Botão do meio/duplo clique informado sem iniciar pan.
12. Transições Axes/Figure, teclas no mapa sob o cursor e ciclos g/G.
13. Viewer usa RGBA sem codecs PNG/cópia inicial e fecha a imagem substituída.

Tempo e memória das sete operações desktop têm um experimento separado,
com workers seriais novos e comparação de pixels/vistas antes/depois. Veja
[medidas e limites](viewer-performance.md). A duração dos smokes não é
benchmark; a pintura visível/input físico continua fora dessa validação.

O [pan ao vivo](pan-interaction.md) recebeu um smoke adicional de nove cenários:
limites e ticks durante motion, moldura fixa, buffer fresco, release sem salto,
origem congelada, histórico e botão direito. A referência direta inclui 60
gestos selecionados; toolbar/tooltip agora têm 28 checks por instalação.

O diálogo de salvar é substituído por um caminho temporário no teste; arquivos
são realmente gerados. Cancelamento também é simulado. Não é teste visual do
diálogo nativo. A primeira renderização desse mapa pequeno está registrada,
mas uma amostra não mede latência típica nem bases densas.

## Contratos comparados diretamente com Matplotlib

`tools/inspect_tk_events.py` instancia um canvas TkAgg real e registra os
[resultados da referência](tk-events-reference.json). Regressões consomem esse
arquivo sem importar Matplotlib. Foram comparados quatro deltas de roda do
Windows, dois botões de roda Linux processados pelo handler da referência,
coordenadas de display, presença de renderer e duas emissões com edição dos
callbacks. A execução foi no Windows; não equivale a executar em Linux.

- `scroll_event.step` conserva `delta / 120`, incluindo frações; botão é
  `up`, `down` ou `None`. Delta zero não altera vista nem cria histórico.
- Eventos de roda fora dos Axes também são entregues, com `inaxes=None`.
- `draw_event.renderer` informa a Scene própria. Não é um renderer Agg.
- Canvas sem GUI e Tk usam a lista de assinantes capturada no início da
  emissão, como a referência: conectar/desconectar dentro de um callback afeta
  eventos seguintes. O callback já capturado recebe o evento atual.

São contratos selecionados, não equivalência completa de eventos. Teclado,
modificadores/botões, enter/leave e keymaps foram ampliados com
[referência direta](viewer-input.md); picking e seleção permanecem pendentes. A Azimlib
oferece zoom pela roda como conveniência própria; a toolbar padrão Matplotlib
não ativa esse zoom automaticamente apenas por emitir scroll_event.

## Executar e validar distribuição

Na raiz do projeto, após instalar as dependências apropriadas:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python tools/smoke_artist_tk.py
python tools/smoke_viewer_tk.py
python tools/smoke_component_lifecycle_tk.py
python tools/smoke_composition_tk.py
python tools/smoke_series_tk.py
python -m build
python tools/smoke_installed_package.py
```

O último comando cria um ambiente novo e instala o wheel com `--no-index
--no-deps`. Confere importação desse ambiente, ausência de Pillow/Matplotlib/GIS,
dados/fontes embarcados e SVG/HTML com Artists/componentes editáveis.
Nenhum caminho de código fonte é acrescentado ao subprocesso.
Linux pode usar `xvfb-run -a python ...` para os smokes desktop.

## CI e trabalho restante

A configuração contém 15 combinações: Windows, Linux e macOS × Python
3.10–3.14. Cada job executa suíte, build e instalação limpa do wheel. Um job
desktop adicional por sistema, em Python 3.12, executa os cinco smokes Tk;
Linux utiliza Xvfb. Esses jobs não importam Matplotlib.

**A CI remota ainda não foi executada.** Faltam resultados efetivos dos runners,
conferência manual de aparência/input nativo, comparação visual da janela com
Matplotlib e medições desktop em bases densas. A validação local avança o quinto
critério da 0.2.0, mas não o fecha nem antecipa urbano/3D/publicação.

Há também [sete cenários de lifecycle](component-lifecycle.md) em Tk real
oculto: edições agrupadas, texto interno ocultável, substituição/desconexão de
componentes, troca de norm/ticks e clear. São edições programáticas, sem medir
aparência/input físico. O primeiro draw agora ocorre após o registro de
callbacks/canvas. Mais [14 cenários de composição](sizing-composition.md) verificam
dimensões/DPI, três títulos, erro inicial e fechamento em callback.
