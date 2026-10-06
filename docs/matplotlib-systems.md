# Sistemas de referência e evolução da Azimlib

Referência inspecionada diretamente: Matplotlib 3.11.2 instalado em ambiente de
desenvolvimento separado. `tools/inspect_reference.py` registra 27 módulos e
894 símbolos públicos em `matplotlib-reference.json`. A inspeção não copia o
backend nem inclui Matplotlib como dependência da biblioteca.

O objetivo é manter o vocabulário e a organização familiar de Figure, Axes e
artistas, acrescentando coordenadas, projeções e componentes cartográficos.
Não há promessa de compatibilidade integral ou igualdade de pixels nesta versão.

| Sistema do Matplotlib | Fundação atual na Azimlib | Próxima evolução |
|---|---|---|
| pyplot e gerenciamento de figuras | seleção por número/nome/sca, subplot/mosaicos, show/close, ion/ioff e conveniências | integração ampliada de event loop |
| Figure, Axes e composição | GridSpec raiz/filhos/spans/pesos, mosaicos aninhados, compartilhamento, rótulos globais, inset, dimensões/DPI, tight/constrained próprios | múltiplos grids raiz, SubFigure e compressed layout |
| Artist, Text, Line2D, Patch | Artist próprio, Layer/Text/Spine/Legend, ScatterCollection editável, ownership, stale, callbacks, setp/getp, edição de linhas e relim/autoscale_view | outras classes especializadas, propriedades completas, picking e seleção |
| Paths, patches e collections | primitivas próprias, polígonos com buracos, paths, círculos e dez hachuras | coleções em lote, símbolos reutilizáveis e padrões customizados |
| Cores, Normalize e ScalarMappable | normalizadores próprios, tabelas CC0 e callbacks de norm compartilhada/mappable para colorbars | normalizadores adicionais, reclassificação discreta, RGBA e arrays mascarados |
| rcParams e style sheets | defaults validados, rc_context, arquivos locais, style.use/context empilhados/reset e ciclos próprios condicionais | discovery, rcParams/ciclos de outras classes mais amplos e novos perfis |
| Axis, ticker e scale | ticks maiores/menores, grades por grupo/eixo, locators/formatters próprios, graus/hemisférios/DMS, labels, spines, tick_params, autoescala/margens, ScalarFormatter científico/offsets editáveis e EngFormatter SI | objetos Tick completos, MathText/TeX, sticky_edges, escalas completas e unidades extensíveis |
| transforms | projeção forward/inverse, CRS e viewport próprio | grafo componível data/projetado/axes/figure/display e inversas |
| Grid e coordenadas | graticules opcionais maiores/menores, controle X/Y e formatação N/S/E/W | interseção exata de graticules com bordas curvas |
| Legend e colorbar | múltiplas colunas, handles compostos, best/bbox_to_anchor, textos/frame editáveis, colorbar compartilhada, cax, tickers e atualização de norm/clim | handlers customizados e regeneração de legendas temáticas |
| Text, fonts e annotations | fontes DejaVu, rotação, multiline, halo, callout, labels na direção local de linhas, colisões com annotations/insets, prioridade por atributo e filtro por extensão | texto curvo por glifo, shaping complexo, posicionamento global otimizado |
| Eventos e navegação | callbacks de mouse/teclado/desenho, pan/zoom/home/history com estados de autoescala | picking, seleção de features, atualização incremental e eventos padronizados |
| Backends e canvas | SVG próprio, Pillow próprio, Tk desktop, HTML explícito | backend Qt, PDF e cache de renderização |
| Widgets | toolbar, configuração de subplots e minimapa opcional | selectors, sliders, botões e controles de camadas |
| Animation | ainda não implementada | atualização de dados, blitting e exportação temporal |
| Image, contour, tri e raster | densidade angular, imagens/meshes/vetores editáveis, marching squares e hillshade | raster georreferenciado, RGB/máscaras, triangulação, edição de contornos, contourf e resampling |
| units, dates e escalas não lineares | graus e CRS explícitos; na 0.3.0 dev, unidades/modelos, geodesia elipsoidal e UTM regional próprios | datas, escalas de Axis e unidades automáticas |
| mplot3d, polar, axisartist e toolkits | fora desta primeira fundação | avaliar por caso; não são pré-requisitos para cartografia 2D |
| Testes e distribuição | testes numéricos, exportação, independência e componentes | baselines visuais, benchmarks, versões de dados e CI multiplataforma |

Séries e estilos têm [contratos diretamente registrados](series-styles.md):
plot com grupos/matrizes/lookup data, composição de ciclos, contexto/reset,
folha local e defaults da legenda. Propriedades completas, masks/units e
compatibilidade integral permanecem fora deste subconjunto.

## Da decomposição visual ao mapa completo

`examples/components.py` reúne os equivalentes dos nove elementos da imagem de
referência: título, legenda, área do mapa, labels de longitude/latitude, ticks,
grid e três séries com cores, traçados e marcadores diferentes. Acrescenta
camadas territoriais, rios, annotation, escala e rosa dos ventos. Todos são
adicionados explicitamente. Não inclui minimapa por padrão.

```python
import azimlib.pyplot as plt

with plt.rc_context({'axes.titlesize': 16, 'lines.linewidth': 2}):
    fig, ax = plt.subplots(subplot_kw={'projection': 'mercator'})
    ax.map('brazil')
    line, = ax.plot([-60, -50, -40], [-20, -15, -10], 'o--', label='Rota')
    title = ax.set_title('Brasil')
    title.set_color('#222222')
    ax.set_xticks([-70, -60, -50, -40])
    ax.tick_params(direction='out', labelsize=9)
    ax.spines['top'].set_linewidth(1)
    ax.grid(step=10)
    ax.legend([line], ['Rota demonstrativa'], loc='upper left')
    ax.scale_bar()
    ax.compass()
    fig.savefig('brasil.svg')
    plt.show()
```

## Caminho para o mapa de hidrovias

1. **Acabamento:** finalizar métricas/layout, offsets dinâmicos no HTML, handlers de legenda
   compostas e escala segmentada configurável; manter exemplos de comparação.
2. **Simbologia cartográfica:** largura/cor/traçado por atributo, labels sobre
   linhas, prioridade e prevenção de colisões. As categorias devem gerar legendas
   com a mesma simbologia, sem exigir desenho manual dos exemplos.
3. **Dados e semântica:** conectar cada trecho a uma fonte versionada de
   navegabilidade, com categoria, situação e data. Os rios Natural Earth atuais
   não fornecem todas essas classes. As rotas coloridas do exemplo são
   esquemáticas e não representam hidrovias classificadas.
4. **Escala e desempenho:** recorte por viewport, índice espacial, simplificação
   por resolução e cache antes de aumentar o detalhe de rios e municípios.
5. **Validação:** mapa completo com testes de geometria, escala, classificação,
   legenda, legibilidade e exportação; depois repetir o processo com outros temas.

Cada etapa deve entregar um mapa reproduzível e ampliar os mesmos componentes
públicos. Evita-se uma coleção de funções especiais que só funcionam na demo.

O [inventário detalhado de pendências](pending.md) reúne o trabalho restante.
