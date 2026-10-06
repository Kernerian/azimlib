# Arquitetura

O fluxo não delega cartografia a outro projeto:

```
pyplot / Figure / MapAxes
           ↓
   Layer + estilos + temas
           ↓
FeatureCollection → Geometry → recorte e densificação
           ↓
   Projection + Viewport
           ↓
  Scene (paths/text/circles/rects em pixels)
           ↓
     SVG / RGBA próprio → PNG ou Tk / HTML interativo
```

## Fronteiras dos módulos

- `geometry.py`: geometrias imutáveis, validação, bounds, geodesia esférica,
  corte de antimeridiano e clipping do horizonte ortográfico.
- `io.py`: leitura/escrita GeoJSON e exportação do leitor CSV de `tabular.py`,
  sem dependência de GIS; seleção imutável vive em `geometry.py`. `crs.py`: transformações
  explicitamente registradas, sem inferência silenciosa de datum ou ordem de eixos.
- `projections.py`: projeções próprias com forward/inverse e registro extensível.
- `datasets.py`: acesso por `importlib.resources` a arquivos compactados offline.
- `axes.py`: API pública, limites, construção de camadas, coropléticos e densidade.
- `layers.py`: artistas editáveis; os dados de entrada permanecem imutáveis.
- `components.py`: TextArtist, Spine, Legend e configuração de ticks independentes.
- `config.py` / `style.py`: rcParams validados e contextos restauráveis de estilo.
- `typography.py`: resolução das fontes distribuídas e métricas de texto offline.
- `styles.py`: validação de estilos, aliases e escalas de cores próprias.
- `colors.py` / `cm.py`: normalizadores, paletas e ScalarMappable compartilhado.
- `colorbar.py` / `colorbar_render.py`: objeto editável, layout, ticks e gradiente.
- `hatches.py`: padrões vetoriais recortados por even-odd, inclusive buracos.
- `label_layout.py`: métricas tipográficas, índice de colisões e prioridade global.
- `layout_engine.py`: limites das mesmas primitivas de títulos/ticks/componentes,
  reservas de margens/gaps em um GridSpec raiz com spans/pesos; engines tight/constrained próprios.
- `gridspec.py`: alocação de células, proporções, seleções retangulares e herança de parâmetros da Figure.
- `fields.py`: grade escalar, marching squares, topologia de contornos e hillshade.
- `viewport.py`: espaço projetado em metros para pixels, com escala isotrópica.
  Limites projetados das classes internas são reutilizados em cache limitado;
  o teste conservador de visibilidade cilíndrica não modifica a geometria.
- `projected_paths.py`: LRU de paths float64 imutáveis, separado de estilos/cenas,
  com orçamento de payload/entradas e referência fraca à geometria original.
- `render_map.py`: transforma dados geográficos em primitivas da cena, compõe
  rótulos e ornamentos e mantém metadados dos viewports para a navegação.
- `scene.py`: contrato de backend sem coordenadas geográficas ou bibliotecas externas.
- `renderers/svg.py`: serialização vetorial própria. `renderers/pillow.py`:
  composição raster própria; Pillow fornece buffers, operações de pixels e fontes.
  render_image entrega um RGBA pertencente ao chamador; render_png apenas o
  codifica e fecha. O viewer usa esse buffer diretamente, sem PNG intermediário.
  Fontes DejaVu são recursos genéricos licenciados, não código de Matplotlib.
- `renderers/_coverage_native.py`: extra `accelerate` opcional. Numba compila
  os nossos loops de recorte/cobertura, sem fastmath; segmentos, discos, fontes,
  projeções e composição continuam próprios. Não é um backend de mapas.
  Sem o compilador, o kernel Python permanece funcional. A compilação a frio
  e sua memória são custos explícitos; não há cache JIT gravado em disco.
- `navigation.py`: histórico e cálculos de limites compartilháveis entre interfaces.
- `backends/tk.py`: janela desktop, toolbar, eventos, preview de arraste, diálogo
  de salvar e minimapa opt-in. Renderiza exclusivamente Scenes próprias.
  Conserva apenas a imagem corrente; fecha a anterior após substituição e a
  corrente ao fechar a janela. Home recompõe a vista por Navigation.
- `backends/_navigation_process.py`: subprocesso de pixels por pipe RGBA privado;
  não recebe Figure/Artists nem altera projeções. O extra gui usa aggdraw genérico
  para preencher polígonos de stroke próprios e NumPy para comparar vértices.
  Tiles e métricas/fontes têm caches limitados; textos preservam amostragem 3x.
  `renderers/_render_control.py` interrompe frames precisos obsoletos. O processo
  fecha junto do viewer; `savefig()` segue a saída precisa sem UI/processo.
- `viewer.py` e `assets/viewer.js`: alternativa autossuficiente com pan, zoom,
  seleção retangular, histórico e visão geral. Não usa Leaflet, D3 ou mapas remotos.
- `figure.py`: composição da figura, exportação atômica e exibição.
- `legend_layout.py`: colunas, amostras compostas, âncoras e escolha heurística
  de posição. Figure compõe colorbars compartilhadas e eixos cax sem backend externo.
- `ticker.py` e `axis.py`: posicionamento/formatação próprios, controlador
  de ticks maiores e delegação dos eixos reservados para colorbars.
- `pyplot.py`: conveniência estatal sobre os mesmos objetos públicos.

## Extensão

Novas projeções implementam `Projection.forward`, `Projection.inverse` e recebem
um nome via `register_projection`. Novos leitores produzem FeatureCollection;
não precisam conhecer renderizadores. Novos backends consomem Scene; não precisam
implementar projeções. Novas camadas entram antes da cena, preservando seleção
de features, estilos e legendas. Isso permite adicionar raster, classificação
avançada ou layouts sem acoplar tudo ao GeoJSON.

Decisões deliberadas desta fundação: stdlib no núcleo, zero rede ao usar o pacote,
camadas ordenadas de forma estável, validação explícita, tipos geográficos imutáveis,
arquivos de origem com checksums e escrita de exportação por substituição atômica.

Não se simplifica a geometria nas exportações estáticas. O cache limitado de
vértices projetados cobre linhas/polígonos nas seis projeções internas exatas;
scatter/campos/labels e subclasses seguem o caminho atual. Dados muito detalhados podem ser lentos, especialmente
na saída raster. O PNG agora compõe tiles locais por primitiva, recortados ao
viewport, e reutiliza fontes durante o render. Isso evita buffers do tamanho
da figura por marcador. O kernel próprio de strokes pode compilar lotes
numéricos limitados pelo extra opcional `accelerate`; não há aceleração GPU.
`tools/benchmark_raster.py` mede composição e rasterização separadamente.
`tools/benchmark_maps.py` amplia a medição para mapas completos, SVG, zoom e
alocações Python. O renderer tem caches limitados de amostras angulares e
tabelas de alpha, mantendo coordenadas/cobertura exatas. A comparação alternada
em `tools/compare_raster_versions.py` é somente de desenvolvimento; snapshots
em tools/baselines não participam do runtime nem do wheel. Veja [desempenho](performance.md).
Geometry/FeatureCollection imutáveis reutilizam bounds; exportações e desktop
podem descartar linhas/polígonos cilíndricos certamente invisíveis, mantendo
callbacks e índices de features. HTML conserva todos os dados da cena para pan.
`spatial.py` implementa uma hierarquia STR imutável, caixas float64 compactas
e o cache de envelopes projetados por
coleção (quatro projeções), consultado em camadas cilíndricas elegíveis. Mantém
ordem, overrides, envelopes ambíguos e varredura de callbacks; a query não é
interseção topológica. Veja [índice](spatial-index.md) e
[limites desta otimização](viewport-performance.md).
Veja também [reutilização dos paths](projected-paths.md), que preserva cortes
e precisão, recalcula estilos/coordenadas de tela e não mantém a fonte viva.
