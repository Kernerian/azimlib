# Componentes, regiões e visibilidade

## Convenções familiares

O Matplotlib aceita `ax.legend(title='Legenda')`. O título é opcional: `ax.legend()`
não acrescenta a palavra Legenda. Ocultar uma linha não remove automaticamente
sua entrada da legenda; a visibilidade da legenda é independente. Essas regras
foram conferidas diretamente no Matplotlib 3.11.2 instalado e testadas na Azimlib.

```python
scale = ax.scale_bar()
north = ax.north_arrow()
legend = ax.legend()                   # sem título automático
locator = ax.overview(context='brazil')

scale.set_visible(False)
assert not scale.get_visible()
scale.set_visible(True)
locator.remove()                      # desanexa o componente do mapa
fig.canvas.draw_idle()                # atualiza uma janela já aberta
```

`set_title`, `set_xlabel`, `set_ylabel`, `subtitle`, `fig.text` e `fig.suptitle`
retornam textos editáveis com visibilidade. Camadas, grid, annotations e labels
oferecem `set_visible`, `get_visible` e `remove`. Legenda, escala, norte/rosa,
minimapa e colorbar também retornam componentes com essas operações.
Textos do mapa oferecem posição editável conforme seu sistema; annotations
distinguem destino xy de texto xyann. Veja [edição de textos](text-edits.md).
Axes e insets aceitam `set_visible`; `set_axis_off()` controla apenas o frame e
os ticks do mapa. Cada spine tem visibilidade própria; labels dos ticks são
controlados por `tick_params(labelbottom=False, ...)`.

Não há checkbox automático no toolbar, assim como a visibilidade de Artists
não cria automaticamente um checkbox no Matplotlib. A aplicação pode conectar
teclas ou controles a `set_visible()` via `mpl_connect`. O exemplo `regions.py`
usa 1=escala, 2=orientação, 3=legenda, 4=grid, 5=minimapa (quando presente).
Os atalhos padrão de pan/zoom/home/salvar permanecem disponíveis.

As extensões cartográficas não existem como esses componentes no núcleo do
Matplotlib. A Azimlib adota o padrão de uso de artistas, mas não declara
compatibilidade integral com todos os objetos e parâmetros do Matplotlib.

## Escala, norte e minimapa

A largura da caixa da escala acompanha o envelope da barra e dos textos.
A barra fica centralizada, com margens simétricas dimensionadas pelo rótulo
mais largo e uma folga curta de meia fonte além do conteúdo. Rótulos de tamanhos
diferentes podem deixar um pouco mais de espaço junto ao menor; o modo compacto
mede somente o total/unidade e a barra presentes. A altura compacta remove a
linha ausente de unidade. Cada desenho
recalcula caixa e distância na posição final após editar fonte, unidade, length,
vista ou tamanho da figura. As graduações passam de três para duas/uma quando
necessário para evitar colisões, mantendo a fonte escolhida.

- **Escala:** mesma função de desenho de caixa da legenda, com cantos arredondados,
  borda, fundo, transparência e padding. A barra é preta/branca por padrão e sua
  unidade aparece dentro da caixa. Mede distância esférica local na latitude
  onde está desenhada, não uma escala única exata para toda a projeção.
- **Norte:** seta de duas metades, com largura proporcional à altura; direção
  calculada na projeção. Não sofre alongamento pelo aspect ratio geográfico.
- **Rosa dos ventos:** oito braços simétricos; N/S/E/W centrados nos eixos
  respectivos. `compass()` e `north_arrow()` são componentes independentes:
  adicionar, editar, ocultar ou remover um não substitui nem altera o outro.
  O padrão da rosa é upper left e o da seta é upper right; posições explícitas
  prevalecem. Nada aparece por padrão. Uma nova chamada da mesma função troca
  apenas a instância anterior daquele tipo e a desconecta da figura.
- **Minimapa:** contexto fixo, fundo escurecido fora da vista atual e retângulo
  preto de foco. A mesma composição aparece no PNG, SVG, Tk e HTML. A caixa
  representa a janela projetada do mapa; em projeções não cilíndricas não é
  necessariamente um retângulo de longitude/latitude.

```python
fig, ax = plt.subplots(projection='mercator')
ax.state('SP')                         # também 'BR-SP' ou 'São Paulo'
locator = ax.overview(context='brazil', shade_alpha=.45)
ax.zoom(2.3, center=(-47.4, -23.3))
ax.scale_bar(framealpha=.8, edgecolor='#cccccc')
ax.north_arrow(size=36)
fig.savefig('estado.svg')
plt.show()
```

```python
arrow = ax.north_arrow(loc='upper right')
rose = ax.compass(loc='upper left')
rose.set(size=28, color='black', loc='lower right')
rose.set_visible(False)  # A seta continua visível.
arrow.remove()          # A rosa mantém seu próprio estado.
```

Ambos retornam OrientationIndicator com set/get_loc, set/get_size,
set/get_color, set_visible, remove e in_layout. `setp` agrupa edições;
valores de posição/tamanho inválidos são rejeitados antes de alterar o componente.
Os dois usam norte local calculado pela projeção e têm tamanhos físicos em pontos.
Veja o [exemplo de coexistência](../examples/orientation.py).

No HTML portátil, Mercator/equiretangular contínuas recalculam a escala após
pan/zoom, preservam as métricas de fonte e reancoram norte/rosa sem esticá-los.
Uma escala explícita que não cabe é ocultada com aviso; Home restaura os
componentes iniciais. Outras projeções ainda ocultam esses ornamentos após
navegar. Veja [contratos](portable-navigation.md) e o
[exemplo interativo](../gallery/portable-components.html).

## Catálogo resumido de componentes

- **Figure:** canvas, dimensões, DPI e fundo que reúnem os mapas.
- **MapAxes:** área projetada do mapa, extensão geográfica e viewport.
- **Frame e spines:** contorno do mapa e controle de cada borda.
- **Subplots:** vários mapas organizados na mesma figura.
- **Inset map:** mapa secundário com projeção/vista próprias dentro de outro.
- **Minimapa/overview:** contexto geral sombreado com foco preto da vista atual.
- **Título:** texto principal de um mapa.
- **Subtítulo:** segunda linha de informação acima do mapa.
- **Suptitle:** título comum a toda a figura.
- **Labels de eixos:** nomes/unidades de longitude e latitude.
- **Ticks maiores e menores:** marcas e números/graus posicionados nos eixos.
- **Grid/graticule:** linhas opcionais de longitude e latitude.
- **Legenda:** símbolos, linhas e categorias com título opcional.
- **Colorbar:** escala de valores/cores, vertical ou horizontal, com ticks e rótulo.
- **Barra de escala:** distância local representada por segmentos, com caixa editável.
- **Seta de norte:** indicador direcional com N.
- **Rosa dos ventos:** símbolo de oito pontas com N/S/E/W, independente da seta.
- **Textos livres:** notas em coordenadas geográficas, de Axes ou da Figure.
- **Labels geográficos:** nomes por atributo, prioridade e prevenção de colisões.
- **Annotations:** texto associado a uma posição, com conexão/seta opcional.
- **Callouts:** chamadas com caixa e ligação a uma localização.
- **Caixas informativas:** textos em painel com fundo para notas/contexto.
- **Camadas territoriais:** países, estados, fronteiras, costas e divisões fornecidas.
- **Camadas naturais:** rios, lagos e fundo de oceano.
- **Camadas viárias:** estradas e municípios fornecidos como dados do usuário.
- **Pontos e marcadores:** posições com forma, área, borda, cor e símbolo de texto.
- **Linhas, curvas e rotas:** traçados, setas e trajetos geodésicos.
- **Polígonos:** áreas com buracos, preenchimento, bordas e hachuras.
- **Camadas temáticas:** coropléticos, categorias, pontos proporcionais e densidade angular.
- **Campos escalares/mesh:** células geográficas coloridas ou imagens escalares.
- **Isolinhas e clabel:** contornos de valores e seus rótulos.
- **Hillshade:** campo de iluminação para representar relevo.
- **Quiver:** setas de direção/intensidade leste/norte.
- **Toolbar e cursor:** pan, zoom, histórico, home, salvar, ajustes de subplots e coordenadas.

Esta lista distingue componentes de composição, camadas de dados e controles
do viewer. Não são todos tipos específicos de Artist do Matplotlib. Grid,
legenda, colorbar, escala, orientação e overview precisam ser adicionados
explicitamente; não surgem como decoração automática.

O Tk recalcula composição e escala depois da navegação. No HTML, o minimapa
atualiza o foco e aceita recentering; a cena principal permanece uma exportação
sem conexão com Python. A escala e a orientação são ocultadas ao sair da vista
inicial, pois ainda não são recalculadas nesse backend. Para um mapa final com
ornamentos corretos, navegue/defina limites em Python ou use o desktop e salve.

## Todos os elementos atualmente disponíveis

A grade começa desligada (`rcParams['axes.grid'] = False`), como no estilo
padrão do Matplotlib. `ax.grid(True)` liga, `ax.grid(False)` desliga e `ax.grid()`
alterna. Argumentos de estilo ligam a grade. O estilo é preservado ao alternar.
`ax.set_axisbelow('line')` coloca a grade acima dos polígonos (zorder 1) e abaixo
das linhas (zorder 2); `True` usa 0,5 e `False` usa 2,5. Valores de zorder
explícitos nas camadas continuam sendo respeitados. Os exemplos chamam grid
explicitamente; a presença neles não é um padrão obrigatório da biblioteca.
No desktop, g percorre os estados da grade maior (desligada/X/X+Y/Y) e G
percorre maior+menor, no mapa sob o cursor; os atalhos são configuráveis.
Veja [eventos e atalhos](viewer-input.md). No HTML, G alterna a grade exportada. No HTML
Mercator/equiretangular, as linhas são recriadas até as bordas da vista ao navegar.

A escala é editável depois da criação, por código:

```python
scale = ax.scale_bar()
scale.set(length=100, units='km', loc='lower right', fontsize=10,
          facecolor='white', edgecolor='black', framealpha=.9)
scale.set_length(50)  # None volta ao comprimento automático
scale.set_visible(False)
fig.canvas.draw_idle()
```

Também há `set_units`, `set_loc`, `set_fontsize`, `set_color`, `set_facecolor`,
`set_edgecolor` e `set_frame_on`. Comprimentos/unidades/tamanhos inválidos são
rejeitados sem alterar o componente. A escala é uma extensão cartográfica
própria: não existe esse objeto específico no núcleo do Matplotlib. Não há um
editor visual de propriedades da escala no toolbar.

Os números da escala se adaptam automaticamente ao espaço, usando as métricas
da fonte escolhida. Quando há largura suficiente, aparecem zero, metade e total.
Se esses rótulos colidiriam, a metade é omitida; se nem as extremidades couberem,
aparece um único texto como `100 km`. A fonte não é reduzida e a barra continua
representando a mesma distância local, com os dois segmentos.

No modo de texto único, a caixa também perde a linha inferior ausente: sua
altura diminui, mantendo apenas a folga abaixo da barra. A ancoragem no canto
é preservada, e a largura é recalculada na posição final para manter a distância.

Redimensionar a Figure, navegar ou editar fontsize recalcula essa seleção no
próximo desenho Python/Tk. PNG/SVG usam o mesmo plano; HTML recebe o plano da
exportação e mantém suas limitações de navegação descritas acima.
O padding protege o texto dentro da caixa e entra no cálculo da distância na
posição final. Um comprimento explicitamente maior que o espaço geográfico
disponível continua gerando erro; não é encurtado silenciosamente.
Veja [três larguras](../gallery/scale-labels.png) e
[o exemplo](../examples/scale_labels.py).

`plt.show()` abre a janela Tk independente com toolbar e eventos; `savefig()`
exporta somente a figura. `fig.show(backend='browser')` é a alternativa HTML
explícita, sem conexão viva com os objetos Python. Matplotlib também possui
backends interativos, mas esta implementação não é um backend Matplotlib.

| Grupo | Elementos |
|---|---|
| Figura e mapa | fundo da figura, fundo do mapa/oceano, frame, bordas individuais, múltiplos mapas/subplots, insets |
| Coordenadas | labels dos eixos, ticks maiores, labels numéricos ou angulares, grid/graticule, coordenadas do cursor no viewer |
| Texto | título, subtítulo, título da figura, textos livres, nomes geográficos, rótulos por atributo, annotations, callouts, caixas informativas |
| Leitura do mapa | legenda, título opcional da legenda, exemplos de linha/marcador/polígono, colorbar, escala, seta de norte, rosa dos ventos, minimapa/contexto com foco |
| Território | países, Brasil, 27 unidades federativas brasileiras, estado individual, fronteiras, costas |
| Hidrografia | rios, lagos, fundo de oceano; bases generalizadas offline |
| Geometria e símbolos | pontos, marcadores, símbolos de texto, linhas, curvas quadráticas, rotas geodésicas, setas, polígonos e buracos |
| Temáticos | coropléticos, categorias, valores por região, pontos proporcionais e densidade angular suavizada |
| Científicos | normalizadores compartilhados, colorbar vertical/horizontal, campos escalares, isolinhas, hillshade e vetores leste/norte |
| Dados do usuário | GeoJSON, municípios e estradas fornecidos pelo usuário; esses dois últimos não têm base embutida |
| Viewer | pan, zoom, home, voltar/avançar, salvar PNG/SVG, configurar subplots, atalhos e callbacks |

Estilos incluem cor, espessura, opacidade, traçados, caps/joins, z-order,
formas/tamanhos de marcadores, rotação, fontes/peso/itálico, alinhamento,
fundo/halo de texto, dez padrões de hachura e estilo por feature. Labels usam
métricas da fonte, prioridade global e posições alternativas; não há texto
curvo nem layout tipográfico completo. Veja [cores e campos](scientific.md).

## Próximos avanços

Esta etapa acrescentou seleção direta de estado, visibilidade uniforme e um
minimapa compartilhado entre exportação e viewer. As próximas fundações são:
texto curvado glifo a glifo e offsets científicos,
cache/recorte de dados para navegação mais rápida. Legendas em colunas e
colorbars compartilhadas/cax já estão disponíveis; veja [composição](composition.md).
Locators/formatters para mapas e colorbars também já estão disponíveis; veja [ticks](ticks.md).
Direção local de rótulos e ticks/grades menores já funcionam;
veja [rótulos](labels.md) e [ticks menores](minor-ticks.md).
Raster georreferenciado, ícones de imagem, animação, 3D, PDF e backend Qt
ainda são planejados, não componentes disponíveis nesta versão.
