# Visualizações e dados necessários

Os nomes abaixo representam aplicações cartográficas; muitos compartilham
os mesmos artistas. A biblioteca não inventa dados de população, clima ou
terreno. Os exemplos científicos usam dados sintéticos identificados.

| Tipo | Implementação atual / evolução |
|---|---|
| Político | map/countries/states/state/borders; municípios próprios via GeoJSON |
| Físico | rivers/lakes/coastlines, campo escalar de terreno fornecido pelo usuário |
| Coroplético | choropleth, bins ou contínuo, norm e colorbar |
| Categórico | categorical, estilos por feature e legenda |
| Pontos | scatter, marcadores/símbolos, textos e labels |
| Bolhas proporcionais | scatter(s=valores): área do marcador em pt² |
| Rotas | line/plot/route, curvas e setas |
| Rotas geodésicas | route(geodesic=True), esfera própria |
| Heatmap | imshow/pcolormesh com intensidade fornecida |
| Density map | density: contagem + suavização em grade angular |
| Flow map | quiver para vetores; rotas com larguras fornecidas; sem grafo/OD especializado |
| Isolinhas | contour e clabel, marching squares próprio |
| Raster | campo escalar matricial por imshow; GeoTIFF/RGB/satélite/resampling planejados |
| Relevo/hipsometria | cmap terrain + campo de altitude fornecido |
| Hillshade | fields.hillshade + imshow; unidades físicas explícitas |
| Topográfico | combinação de campo, hillshade, contour, rios e labels |
| Climático | campo escalar, coroplético ou vetores com dados externos |
| Hidrográfico | rios/lagos offline + bacias/drenagem externa; sem algoritmo hidrológico |
| Rodoviário | roads(data) + estilo/hierarquia por feature |
| Urbano | GeoJSON fornecido de ruas/bairros/edifícios + labels/hachuras; bases/APIs especializadas e navegação densa planejadas no [roteiro urbano](urban.md) |
| Populacional | choropleth, proportional scatter ou density com dados externos |
| Elevação 3D | planejada: câmera, depth buffer e artistas de superfície próprios |
| Temporal | callbacks/editáveis no desktop; animação/frames/time slider especializados planejados |
| Atlas | subplots e várias figuras; exportação paginada/PDF planejada |
| Regional focus | state, set_extent/zoom + overview |
| Inset/overview | inset_axes e overview com foco preto/sombra |
| Minimalista | componentes opt-in, set_axis_off e estilos explícitos |
| Dark map | style.context('dark_background') + estilos das camadas |
| Scientific map | unidades, labels, escalas, colorbars e exportação PNG/SVG |
| Infográfico | textos, annotations, callouts, marcadores, inset e composição própria |

O anexo de nuvem 3D exige uma fundação de câmera/profundidade; não corresponde
ao renderer cartográfico 2D atual. O globo ortográfico do exemplo já combina
projeção esférica, geometrias, graticule, rotas e vetores projetados. No momento,
pan/zoom não equivalem a girar uma câmera 3D.

Exemplos executáveis: [scientific.py](../examples/scientific.py),
[components.py](../examples/components.py), [regions.py](../examples/regions.py)
e [gallery.py](../examples/gallery.py) (thematic/density/projections/hydrography).
O [catálogo do corte](release-gallery.md) fornece reprodução conjunta, fontes
e limites das visualizações.
