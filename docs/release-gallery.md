# Galeria do corte 0.2.0: reprodução e referências

> Evidência histórica: resultados CI, tempos e hashes abaixo pertencem aos
> snapshots originais. A preparação BSD/licenças/privacidade altera arquivos;
> os checks atuais e a relação de hashes publicados estão em
> [preparação de publicação](publication-readiness.md). Esses resultados não são uma nova execução CI.

O catálogo abaixo reúne exemplos executados com a fundação 0.1.0 alpha.
Ele cobre as famílias do [catálogo 2D](artist-scope-0.2.md), com dados reais
generalizados de Natural Earth e campos/rotas/valores demonstrativos identificados.
Não usa Matplotlib no runtime. [Como começar](getting-started.md).

## Reproduzir sem abrir janelas

Na raiz do projeto, após instalar `.[png]`:

```bash
python tools/release_gallery.py
python tools/release_gallery.py --cases state focus colorbar-horizontal --dpi 200
python tools/release_gallery.py --gallery gallery-local --report gallery-local/report.json
python tools/api_reference.py
python tools/check_documentation.py --output doc-examples
```

O primeiro comando produz PNG/SVG estáticos e HTML separado para **19 exemplos
em 100 e 200 DPI**. Cada caso tem origem, dimensões, quantidade de textos,
clipping, hashes e overflow de texto registrados em
[release-gallery.json](release-gallery.json). SVG é lido como XML e seus textos
são comparados com a cena; PNG é conferido por dimensões e pixels RGBA.
Isso complementa as regressões de composição/renderização, sem substituir
inspeção visual de uma janela nativa ou de qualquer viewer SVG externo.

O [wheel instalado](release-gallery-wheel.json) reproduziu os 19 exemplos em
100 DPI com PNG, SVG e HTML exatamente iguais aos de source. O núcleo sem
dependências opcionais e o wheel GUI também executaram os três snippets do
[guia inicial](getting-started.md), produzindo SVGs idênticos. [Auditoria de docs](documentation-check.json).
`python tools/audit_release_gallery.py --wheel-gallery CAMINHO` confere os
hashes dos artefatos/source e os relatórios de reprodução instalados.

![Catálogo visual](../gallery/release-overview.png)

## Exemplos e componentes

| Exemplo a 200 DPI | Código | O que demonstra |
|---|---|---|
| [Brasil: componentes](../gallery/release-components-200.png) | [components.py](../examples/components.py) | Países, estados, rios, três estilos de linha/marcador, legenda, rosa, escala, annotation com halo |
| [Brasil inteiro](../gallery/release-brazil-200.png) | [regions.py](../examples/regions.py) | Extensão completa, componentes adicionados explicitamente |
| [Estado](../gallery/release-state-200.png) / [foco](../gallery/release-focus-200.png) | [regions.py](../examples/regions.py) | São Paulo isolado, zoom, overview sombreado com borda preta |
| [Séries claras](../gallery/release-series-light-200.png) / [escuras](../gallery/release-series-dark-200.png) | [series_styles.py](../examples/series_styles.py) | Séries por coluna, data=, ciclo, edição de losangos D, legenda explícita |
| [Colorbar vertical](../gallery/release-colorbar-200.png) / [horizontal](../gallery/release-colorbar-horizontal-200.png) | [scientific.py](../examples/scientific.py) | Coroplético contínuo e barra vinculada ao mappable |
| [Hachuras](../gallery/release-hatch-catalog-200.png) | [scientific.py](../examples/scientific.py) | Dez padrões básicos, repetições e combinações; polígonos com buracos |
| [Contornos antes](../gallery/release-contours-before-200.png) / [depois](../gallery/release-contours-after-200.png) | [contour_refinement.py](../examples/contour_refinement.py) | Estilos por nível, rótulos inline editáveis, barras de linhas |
| [Terreno](../gallery/release-terrain-200.png) | [scientific.py](../examples/scientific.py) | Campo escalar sintético, hillshade, isolinhas, costa e colorbar |
| [Globo](../gallery/release-globe-200.png) | [scientific.py](../examples/scientific.py) | Ortográfica, graticule, rotas esféricas e vetores; não uma câmera 3D |
| [Formatação vertical](../gallery/release-numeric-vertical-200.png) / [horizontal](../gallery/release-numeric-horizontal-200.png) | [numeric_formatting.py](../examples/numeric_formatting.py) | Notação científica, offset aditivo e eixos editáveis de colorbar |
| [Temático](../gallery/release-thematic-200.png) | [gallery.py](../examples/gallery.py) | Valores por estado, bolhas proporcionais, rotas e inset |
| [Densidade](../gallery/release-density-200.png) | [gallery.py](../examples/gallery.py) | Eventos com seed fixo, contagem suavizada em grade angular |
| [Projeções](../gallery/release-projections-200.png) | [gallery.py](../examples/gallery.py) | Seis projeções próprias do mesmo território |
| [Atlas](../gallery/release-atlas-200.png) | [gridspec_atlas.py](../examples/gridspec_atlas.py) | GridSpec/spans, colorbar compartilhada, mapas e ornamentos independentes |

Cada PNG tem SVG e HTML com o mesmo nome-base. Por exemplo:
[components SVG](../gallery/release-components-200.svg) e
[components HTML](../gallery/release-components-200.html).
A [matriz de layout](layout-acceptance.md) acrescenta 24 composições, fontes
grandes e ticks rotacionados. [Aceite de Artists](artist-acceptance.md) cobre
edições integradas de geometria, scatter, mesh, vetores e contornos. Os exemplos
do catálogo são um corte de reprodução; não toda combinação possível de recursos.

## Comparar com Matplotlib

Matplotlib 3.11.2 está instalado apenas no ambiente de referência. Com esse
ambiente, execute `python tools/release_gallery.py --reference`.

Há duas comparações diferentes:

1. **Mesmo Scene → Agg:** componentes, estado, foco, hachuras e globo em 100 DPI.
   O núcleo Azimlib calcula geografia, layout, hachuras e símbolos; o adapter
   envia os mesmos caminhos/textos ao Agg. Isola rasterização, não valida
   projeções nem o layout nativo Matplotlib.
2. **Axes nativos independentes:** séries claras/escuras e colorbars numéricas
   vertical/horizontal em 100/200 DPI, com chamadas à API de cada biblioteca.
   A referência tem eixos geográficos comuns com aspecto igual. Escala/norte
   são extensões da Azimlib e aparecem apenas no seu painel de séries.

Exemplos: [séries, API/layout nativos](../gallery/release-series-light-200-native-comparison.png),
[colorbars horizontais, API/layout nativos](../gallery/release-numeric-horizontal-200-native-comparison.png),
[componentes, mesmo Scene](../gallery/release-components-100-raster-comparison.png).
Contornos também têm uma [referência nativa específica](../gallery/contour-reference.png).
Regras de rotação foram comparadas em [768 caixas de texto nativas](text-rotation.md).
Diferenças restantes estão no [registro visual](visual-differences.md).

As imagens de comparação incluem uma faixa de identificação; ela não faz parte
de `savefig()`. Nenhum resultado declara igualdade pixel a pixel, rapidez de
primeiro desenho. O relatório automático da galeria não é uma inspeção da
janela Tk; o [verificação visual Windows](viewer-visible-acceptance.md) é evidência separada.
