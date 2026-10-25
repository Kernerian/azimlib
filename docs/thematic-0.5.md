# Fase C — primitivas temáticas da 0.5.0.dev0

Implementação de desenvolvimento sobre a Fase B (`b77b12c92523d203211a3d30e39f09998e5d0816`).
Uma infraestrutura Figure/MapAxes/Layer/ArtistGroup; CPU padrão, zero download
implícito e nenhuma alteração da versão 0.4.0 publicada.

## Uso integrado

```python
import azimlib as azl

fig, ax = azl.subplots(body=azl.MARS, figsize=(7, 5))
ax.set_extent((-12, 12, -8, 8))
context = ax.get_context()
regions = ax.group(name="Scientific scenario", zorder=1)
region = azl.RegionDefinition.polygon(
    [(-8, -5), (8, -5), (8, 5), (-8, 5)],
    context=context, category="Illustrative zone")
regions.add(ax.region(region, facecolor="#d9b676", alpha=0.35))
objects = ax.group(name="Sites", zorder=4)
objects.add(ax.symbols([(-5, -2), (5, 2)], "rover", size=18,
                       labels=["A", "B"], category="Fictional rover"))
path = azl.CartographicPath.bezier(
    [(-5, -2), (-4, 5), (4, 5), (5, 2)], context=context)
objects.add(ax.cartographic_path(path, color="#a95542", linewidth=1.5,
                                arrow="end"))
ax.legend()
fig.savefig("thematic.svg")
```

`import azimlib.pyplot as plt` oferece os mesmos objetos e wrappers
`symbols`, `thematic_region`, `region_bands` e `cartographic_path` no Axes atual.
`Axes.region(RegionDefinition)` usa a primitiva temática; a API anterior
`Axes.region(SphericalRegion)` continua com seu contrato terrestre original.

## Símbolos e procedência

`AssetSource(origin, license, credit, sha256="")`, `SymbolPart` e
`SymbolDefinition` são definições imutáveis reutilizáveis. `symbol_catalog()`
devolve uma cópia do registro de 18 desenhos programáticos próprios: city,
village, port, gold, salt, ivory, fortress, mine, monument, landing, rover,
probe, instrument, battle, temple, base, scientific-point e arrow. São sinais
demonstrativos, não pictogramas normativos ou marcas de missões.

`SymbolDefinition.from_paths` aceita geometria vetorial autoral; `from_svg`
e `from_png` leem somente um arquivo local explicitamente informado. Origem,
licença e crédito são obrigatórios; SHA informado deve coincidir com o arquivo.
O hash lido fica na definição e os avisos acompanham PNG/SVG/PDF. Declarar uma
licença não prova que o autor tem permissão: é responsabilidade de quem fornece
o asset. Nenhum catálogo externo de ícones foi incorporado.

`ax.symbols(positions, symbol, size=12, size_unit="pt", rotation=0,
anchor="center", offset=(0, 0), labels=None, category="", priorities=None)`
cria SymbolArtist. Tamanho visual e offsets em pontos tipográficos, aspecto
uniforme, ângulo visual anti-horário; a projeção transforma a âncora, não achata
o ícone. `size_unit="m"` define uma largura local geodésica leste/oeste: não é
um polígono científico de área constante. Há recusa de footprints além de 10%
do semieixo ou cruzando o horizonte. Máximo 2048 posições/batch, 262144 vértices
vetoriais instanciados, 256 pt ou 500 km de largura declarada.

Ancoragens: center/bottom/top/left/right ou frações (x,y) da caixa do símbolo,
eixo y visual para baixo. Prioridades maiores desenham depois; não significam
solver de colisões. Labels associados usam o shaping/halo existentes, sem motor
novo de distribuição. Picker fornece os índices dos elementos, preservando
callbacks e remoção. Setters validados: set_size/set_positions/set_symbol/set_labels.
Legenda automática usa label ou category; handles explícitos preservam o ícone.

### Subconjunto SVG seguro

UTF-8, viewBox numérico positivo, svg/g/path/rect/circle/ellipse/line/polyline/
polygon; paths M/L/H/V/Q/C/Z absolutos/relativos; translate/scale/matrix e rotate
sem centro explícito; pintura simples/currentColor. Transformações afins mudam
os pontos do desenho; não há suporte a stroke geométrico complexo ou navegador
SVG. Traços sob transformação não uniforme/skew e matrizes singulares são
recusados; escala uniforme é aplicada também à largura do traço. Curvas são discretizadas em 24 passos/segmento; círculos em 64 segmentos.
Multipart paths com furos exigem fill-rule="evenodd" explícito. Curvas abertas
com mais de dois pontos exigem fill="none". A geometria deve caber no viewBox.

Recusados scripts, DTD, entidades, texto SVG, use/image, URLs/href, fontes,
CSS externo, filtros, máscaras SVG, gradientes SVG e elementos desconhecidos.
Opacidade de composição em grupos SVG é recusada: não se simula composição
isolada por alpha de cada filho. Fill-opacity/stroke-opacity são herdados com
precedência explícita. Aplicar alpha ao Artist continua disponível.
Limites: 256 KiB, 256 nós, profundidade 8, 4096 vértices de controle por path,
16384 vértices totais após amostragem. Recursos fora do subconjunto geram erro.

PNG exige Pillow opcional, arquivo de até 1 MiB, 128x128 pixels, um frame e
algum pixel visível; dimensões verificadas antes da decodificação. RGBA e alpha
parcial preservados, sem APNG. Rotação/redimensionamento gera somente um sprite
limitado (cache LRU de 8 entradas, até 1 milhão de pixels por entrada). A página
não é convertida inteira em bitmap. Cantos transparentes não recebem picking.

## Regiões, máscaras, bandas e gradientes

RegionDefinition recebe Geometry Polygon/MultiPolygon e contexto explícito.
Aceita componentes separados, furos, sobreposições entre Artists, hatches do
motor existente, alpha, contorno, zorder e máscara por interseção exata em carta
angular. `.masked(other)` exige contexto idêntico; a geometria original não muda.
Há validação de auto-interseções, furos inválidos e componentes sobrepostos em
um mesmo MultiPolygon; sobreposição intencional usa Artists separados.
Limite de 2048 vértices por definição e budgets do overlay reutilizado.

Arestas são segmentos em longitude/latitude regional desembrulhada, não geodésicas.
Antimeridiano é dividido pelo projetor existente; símbolos/curvas ocultos pelo
horizonte não atravessam o globo. Interiores com amplitude >=180 graus, regiões
que tocam o polo e projeções não suportadas são recusados explicitamente.
Regiões próximas ao polo podem ser usadas no domínio demonstrado. Nenhum claim
de topologia universal para corpos irregulares/triaxiais ou projeções interrompidas.

`ax.region_bands([(definition, style), ...], semantics="decorative")` cria um
grupo de até 128 áreas autorais. A ordem é explícita e não calcula expansão de
impérios, buffer de influência ou probabilidade. Categorias e geometria vêm do autor.

LinearGradient(start, end, colors, semantics, steps=32, values=None, unit=None,
meaning="") define t=clamp(dot(p-start,end-start)/norm(end-start)^2,0,1), em
coordenadas angulares da mesma carta. Cores de endpoints interpoladas em sRGB.
O autor escolhe decorative, quantitative ou uncertainty. As duas últimas exigem
valores/unidade/significado; o efeito não gera nem certifica um campo científico.
Exibir em 2..128 faixas é aproximação visual declarada, com furos/máscaras exatos
na topologia representada. Não há gradiente radial ou campo implícito inventado.

## Caminhos e medidas

CartographicPath.polyline, .bezier (cúbica) e .spline (Hermite cardinal C1)
são caminhos editoriais em graus lon/lat desembrulhados. Endpoints e controles
permanecem disponíveis; a amostragem é explícita e limitada a 4097 pontos.
Spline pode ultrapassar o domínio; isso gera erro, não clipping científico oculto.
Os segmentos e curvas são projetados novamente quando muda o viewport/projeção.
Não há interpolação em espaço visual projetado nesta fase.

.geodesic(waypoints, context=...) utiliza BodySurface e mantém comprimento da
superfície calculado antes da projeção; .network(RoadRoute, context=Earth)
preserva geometria e métricas do roteador terrestre existente. Não inventa um
grafo marciano. Trajetória física/orbital é recusada e permanece na 0.6.0.

CartographicPathArtist aceita cor/alpha/largura/tracejado/seta do renderer,
path_symbol, spacing e symbol_size em pontos. Símbolos acompanham tangente dos
segmentos projetados e reiniciam em ramos separados por clipping. Máximo 2048
instâncias no caminho. Não são adicionados labels curvos ou fluxos quantitativos
proporcionais com unidade/legenda nesta fase.

get_length(space="surface", unit=METRE) só vale para geodésica/rede;
"sampled_surface" solicita a soma de geodésicas entre amostras, identificada como
tal, inclusive para editorial; "visual" mede pixels de saída dos segmentos
projetados, não distância científica. Não confundir distância 3D ou trajetória.

## Grupos, ownership e interação

ArtistGroup reutiliza os Layers existentes. Visibilidade é AND dos ancestrais;
zorder soma offsets; estilo local da folha > grupo mais próximo > ancestrais.
set_style substitui defaults do grupo, nunca altera dados. set_clip_box aceita
(x,y,w,h) em frações do Axes a partir do topo esquerdo; clips ancestrais são
intersectados e não removem o domínio/horizonte do projetor. Clipping poligonal
compartilhado continua futuro; máscaras explícitas de regiões são funcionais.

set_legend_visible controla inclusão das primitivas temáticas descendentes.
Não cria seções/grupos editoriais na legenda e não promete agrupar toda coleção
legada. Labels associados seguem visibilidade/clipping da folha.
.instantiate(other_axes) compartilha definições imutáveis e cria Artists novos
para o mesmo contexto; estilos locais/visibilidade/clips preservados, callbacks
não copiados. Também permanece a clonagem da geometria simples da Fase A.
Coleções especializadas legadas não suportadas são recusadas. O mesmo Artist
mutável nunca é anexado a dois Axes. Contexto diferente exige redeclaração dos
dados; isso não é transformação física de Terra para Marte.

Picking permanece por folha, callbacks e stale/redraw usam o lifecycle existente.
Ciclos, reparenting implícito e transformações arbitrárias dos dados temáticos são
recusados. Não há picking agregado de grupo. Tk/Qt usam CPU existente; o viewer
HTML navegável recusa camadas temáticas que não pode representar fielmente.
Notebook SVG estático continua disponível. PNG sprites recusam GPU direta;
fallback CPU só ocorre conforme a política explícita já existente.

## Exportação e fidelidade

| Elemento | PNG/CPU | SVG | PDF |
|---|---|---|---|
| Regiões, hatches, rotas e símbolos vetoriais | raster final | paths vetoriais | paths vetoriais |
| Ícone PNG | sprite alpha | PNG embutido, só o sprite | image XObject + soft mask, só o sprite |
| Gradiente temático | faixas sem costuras internas | faixas vetoriais | tile RGBA local do preenchimento, contorno vetorial |
| Texto existente | shaping conforme engine | texto/fontes ou outlines conforme engine | outlines do writer existente |

PDF usa Pillow opcional apenas para o preenchimento de gradiente, evitando
costuras de rasterizadores PDF entre faixas adjacentes. Tile limitado a 1 milhão
de pixels; exceder exige reduzir DPI/tamanho ou escolher SVG. Isso não rasteriza
a página. Gradientes continuam sendo apresentação amostrada, não nova medida.
DPI/tamanho afetam tesselação visual dos ícones e resolução dos sprites; não há
promessa de identidade pixel a pixel entre rasterizadores. Fontes DejaVu e
materiais externos mantêm seus avisos. Costuras ortográficas densas da Fase B
continuam refinamento histórico independente; não foram ocultadas ou corrigidas
com uma reescrita do renderer nesta fase.

## Exemplos e validação

- examples/thematic/historical_trade_map.py: Natural Earth + overlay fictício.
- examples/planetary/mars_exploration_map.py: superfície sintética por padrão;
  --real-data recebe explicitamente o diretório auditado do complemento B,
  verifica o hash na importação e mantém seu frame histórico Viking declarado.
- examples/thematic/primitives_050.py --output DIR: 8 cenas, PNG/SVG/PDF e índice
  HTML local comparável. L alterna o grupo indicado no viewer nativo opcional.
- tools/benchmark_thematic.py: workload fixo, tempos brutos/mediana/p95/variância,
  memória rastreada separada; sem herdar garantias GPU adiadas.
- tests/test_thematic*_050.py: geometria analítica, segurança, ownership,
  atributos físicos/visuais, conteúdo dos renders e exportações determinísticas.

Tolerâncias prévias: Bézier/endpoints <=1e-10 grau, invariância visual de tamanho
<=1e-8 unidade de cena; geodésicas mantêm tolerâncias independentes da Fase B.
Os testes visuais internos não substituem aceite humano final multiplataforma.
Veja [registro da fase](thematic-validation-0.5.md) e [checklist](release-plan-0.5.md).
Fases D–F, labels curvos, locators, temas, composição e validação integral
permanecem abertas. Não iniciar automaticamente a fase seguinte.
