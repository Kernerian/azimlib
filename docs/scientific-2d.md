# Mapas científicos 2D — desenvolvimento 0.3.0

Este guia descreve `dev/0.3.0`, não o pacote estável 0.2.0 do PyPI. A API usa
Artists, norm, callbacks e composição da Azimlib. Não importa nem adapta código
de Matplotlib, ContourPy, SciPy, Rasterio ou bibliotecas cartográficas externas.
Pillow apenas decodifica imagens e auxilia o renderer próprio de PNG.

## Raster escalar e RGB/RGBA

```python
import azimlib as azl
fig, ax = azl.subplots()
image = ax.imshow([[(255, 0, 0, 255), (0, 0, 255, 128)]],
                  extent=(-50, -48, -22, -21), origin='lower')
image.set_data([[(0.2, 0.5, 0.8, 1.0), (0.0, 0.0, 0.0, 0.0)]])
fig.savefig('rgba.svg')
```

RGB/RGBA aceita matriz `(ny,nx,3/4)`: canais inteiros em 0–255, floats em 0–1.
Não misture as duas convenções dentro de um pixel. `ColorImage.get_data()` retorna
canais normalizados RGBA. `None`, NaN ou canal mascarado tornam o pixel
transparente. `alpha` do Artist multiplica alpha por pixel. Não há norm/colorbar
para cores prontas; use um `ScalarMappable` separado se houver uma grandeza física.
`set_data`, `set_extent`, estilos, visibilidade e remoção são editáveis; erro de
validação não troca os dados nem o extent. O extent do Artist não altera limites
do Axes já explícitos. `origin='upper'` coloca a primeira linha ao norte.

`GeoRaster(..., color_mode='auto', mask=...)` detecta escalares ou cores.
`color_mode='rgba'` permite inclusive pixels inteiramente ausentes. `mask` é
booleana com uma entrada por pixel; a cópia imutável também considera NoData,
não finitos ou alpha zero. RGB usa alpha/máscara, não um sentinel escalar NoData.
`read_raster` lê escalares, RGB/RGBA ou paleta expandida pelo codec. GeoTIFF
aceita escalares black-is-zero ou RGB8/RGBA8 contíguo, alpha não associado,
orientação top-left, tags/CRS explícitos do [leitor próprio](formats.md).
BigTIFF, multiframe, YCbCr/CMYK e variantes não implementadas continuam erros.

As células são polígonos projetados pelo mesmo núcleo em PNG/SVG; sem Pillow,
SVG com cores continua funcionando. Isto ainda não é textura GPU ou um
renderer de satélite com milhões de células. Bordas curvas são densificadas;
use resoluções moderadas. Não há mosaico, streaming, COG ou pirâmide de tiles.

## Resampling com cobertura e NoData

```python
raster = azl.GeoRaster([[1, 2], [3, None]], (1, 0, -50, 0, -1, -20))
fine = raster.resample((32, 32), method='bilinear', missing='strict')
sample = raster.sample(-49.5, -20.5, method='nearest')
fig, ax = azl.subplots()
layer = ax.raster(fine)
fig.colorbar(layer, label='Valor')
```

`shape=(ny,nx)`; centros de pixels de destino passam pela transformação CRS
própria e inversa afim da origem. Sem grid explícito, preservam-se cobertura,
rotação/shear e CRS. Mudar CRS exige `extent` ou `affine` de destino.
`extent` está nas unidades do CRS de destino; `affine` usa cantos de pixels.
Nearest seleciona o pixel que cobre o ponto. Bilinear interpola centros,
clampa taps na borda e retorna ausente fora da cobertura semiaberta.

`missing='strict'` mascara se algum tap de peso positivo estiver ausente;
`renormalize` redistribui os pesos só entre taps válidos. RGB interpola cor
premultiplicada e alpha, evitando vazamento de cores invisíveis. Nenhuma
política extrapola para fora da cobertura. Há limite de 16 milhões de pixels
de destino, não uma promessa de desempenho nessa resolução. Um raster UTM,
rotacionado ou sheared pode ser resampled para grid geográfico antes de
`ax.raster`; desenho direto curvilíneo permanece pendente.

## Contornos preenchidos e campos irregulares

```python
fig, ax = azl.subplots()
bands = ax.contourf([-50, -49, -48], [-22, -21],
                    [[0, 1, 2], [0, 1, 2]], levels=[0, 1, 2], cmap='ocean')
bar = fig.colorbar(bands, orientation='horizontal', spacing='proportional')
ax.legend(handles=[bands])
bands.set_levels([0, 0.5, 1, 2])
bands.set_cmap('terrain')
```

`contourf` usa uma superfície linear em dois triângulos SW–NE por célula.
É uma política explícita diferente da interpolação bilinear das isolinhas
`contour`. Qualquer nó ausente exclui a célula inteira. Recortes por intervalo,
cancelamento de arestas compartilhadas e rastreio de fronteiras formam polígonos
com anéis internos reais. Ilhas e furos recebem a regra even-odd dos backends.
Níveis explícitos são fronteiras; um inteiro pede esse número de intervalos
igualmente espaçados. O limite superior final inclui platôs nesse valor.
Valores fora dos níveis não são preenchidos; `extend` da barra só desenha sua
indicação visual, não gera faixas exteriores no mapa.

`FilledContourSet.levels` guarda fronteiras; `cvalues`/`set_array` têm uma entrada
por intervalo. `set_array` recolore, `set_levels` reconstrói geometria retida e
preserva norm/clim. `colors=['red','blue']` usa índices explícitos; nesse caso
níveis novos exigem um novo contourf. Colorbars horizontais/verticais usam as
faixas reais, não a barra de linhas do `contour`. Legendas consultam cores
atuais a cada desenho. Erros não deixam um Artist parcialmente anexado.
`allsegs` aqui agrupa polígonos/anéis por intervalo; não promete o layout de
todos os arrays internos do Matplotlib. Não há corner_mask/Gouraud/contourf
curvilíneo, clipping por limites de município ou atualização de Z in-place.

```python
tri = azl.Triangulation([-50, -48, -50, -48], [-22, -22, -20, -20])
field = [0, 1, 2, 3]
fig, ax = azl.subplots()
filled = ax.tricontourf(tri, field, levels=[0, 1, 2, 3])
interpolate = azl.LinearTriInterpolator(tri, field)
value = interpolate(-49, -21)
```

Delaunay plano regional próprio, determinístico, com predicados normalizados
e desempate cocircular por ordem determinística de inserção. O kernel inicial
é quadrático e limita geração automática a 5.000 nós. Duplicatas, colineares,
quase degenerados não resolvidos e travessia do antimeridiano são rejeitados.
Conectividade explícita valida índices, duplicatas e área; o chamador deve
fornecer uma malha sem sobreposições. Não é triangulação esférica/constrained.
`set_mask` mascara triângulos; nó ausente também os exclui. Interpolação linear
baricêntrica retorna `None` fora do hull e respeita a máscara atual. Artists
são snapshots da malha ao criar; recrie após mudar a máscara. `tripcolor`
aceita cores flat a partir da média de três nós; não implementa Gouraud.

## Densidade, fluxos e relevo

`hist2d(lon,lat,weights=...,bins=(nx,ny),extent=...,density=...)` retorna
`(grid,xedges,yedges,MeshCollection)`. `heatmap` usa o contrato de `imshow`.
`density` com `weights`, `normalization`, `extent` ou bins em par usa a mesma
malha escalar. O caminho antigo sem esses argumentos preserva o Artist
coroplético e sua suavização legados. Pesos novos são finitos e não negativos;
pontos fora do extent são excluídos. A gaussiana nova redistribui cada footprint
na borda para conservar massa. Count soma pesos; probability soma 1; density
integra 1 em graus². **Nenhum deles calcula habitantes/km².** Bins 2–512 por
dimensão; smoothing 0–5 células; zero peso incluído não pode ser normalizado.

`flow(origins,destinations,values,ellipsoid=azl.WGS84)` desenha rotas geodésicas
próprias em lote. Cores vêm de norm/cmap, largura de magnitude no intervalo
clim e `minwidth/maxwidth` em pontos. `set_array`, `set_clim`, `set_norm` e
`set_cmap` atualizam mapas/legendas temáticas; endpoints são fixos. Missing
é invisível; valores negativos são erros. Não inclui grafo OD, bundling ou
roteamento rodoviário. `quiver` conserva componentes leste/norte na projeção;
`legend_elements()` retorna proxies de magnitude e labels em unidades do vetor
(snapshot a regenerar após editar U/V), separados da colorbar de C.

`ax.terrain(Z,extent=...,dx=...,dy=...)` retorna `(ColorImage,ScalarMappable)`:
hipsometria RGB modulada pela iluminação Lambertiana própria. A colorbar é de
elevação; a imagem iluminada é snapshot a recomputar se Z/luz/paleta mudarem.
`ax.hillshade` retorna ScalarImage com limites 0–1. Unidades de elevação, dx e
dy devem ser consistentes, normalmente metros; nunca se inferem metros de
graus. Origin controla o norte do campo. Componha com `contour`, `clabel`, rios,
vetores e componentes opcionais. Não calcula hidrologia nem extrusão 3D.

`ScalarMappable.to_rgba` aceita escalares, matrizes ou imagem RGB/RGBA pronta;
`bytes=True` retorna canais inteiros, `alpha` edita opacidade, `norm=False`
interpreta valores já normalizados. `set_classes` reclassifica coropléticos e
atualiza legendas. BoundaryNorm possui suas próprias classes: troque norm em
vez de chamar set_classes. Limites explícitos são preservados ao trocar array;
chame `autoscale()` para recalculá-los. Nenhum componente surge por padrão.

## Evidência e reprodução

```bash
python examples/scientific_atlas.py --output gallery/scientific-2d/gallery-installed
python examples/composition_atlas.py --output gallery/scientific-2d/composition-installed
python -m unittest tests.test_scientific_foundation
python -I tools/audit_scientific_2d.py --output gallery/scientific-2d
```

A captura pelo auditor exige Python com o wheel de desenvolvimento instalado,
sem editable install/PYTHONPATH de source; exemplos isolados podem usar a fonte.
O auditor atualiza previews/manifests da galeria e escreve o relatório numérico.

[Galeria e proveniência](_static/scientific/README.md),
[testes analíticos](../tests/test_scientific_foundation.py),
[503 casos numéricos/exports](scientific-evidence-0.3.json),
[validação instalada](scientific-validation-0.3.json) e
[smoke Tk](scientific-desktop-0.3.json). Fixtures de terreno/pontos/cores são
originais e sintéticas. Rotas usam Natural Earth public domain como contexto.
Licenças de fontes/paletas já distribuídas permanecem separadas. Resultados
locais não substituem nova CI nos três sistemas nem aceite visual humano.
