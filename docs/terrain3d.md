# Terreno 3D experimental — 0.3.0 em desenvolvimento

Disponível no branch de desenvolvimento, **não no pacote publicado 0.2.0**.
Câmera, matrizes, clipping homogêneo, triangulação, iluminação e depth buffer
são implementados pela Azimlib. NumPy acelera nossas equações; Pillow codifica
imagens e compõe pixels. Nenhum backend de Matplotlib/GIS/3D é utilizado.

## Superfície em coordenadas físicas

```python
import azimlib.pyplot as plt  # import azimlib as azl também funciona

fig, ax = plt.subplots(subplot_kw={'projection': '3d'})
surface = ax.plot_surface(
    [0, 100, 200], [0, 100, 200],
    [[0, 20, 0], [20, 80, 20], [0, 20, 0]],
    horizontal_unit='m', vertical_unit='m', cmap='terrain', shade=True,
)
ax.set_xlabel('Leste (m)')
ax.set_ylabel('Norte (m)')
ax.set_zlabel('Elevação (m)')
ax.set_title('Relevo sintético')
ax.set_vertical_exaggeration(2)
ax.view_init(elev=35, azim=-60, roll=0)
fig.colorbar(surface, label='Elevação física (m)')
fig.savefig('terrain.png')
plt.show()
```

X/Y podem ser vetores de colunas/linhas ou matrizes da mesma forma de Z. Unidades
aceitas: `m`, `km`, `ft` e `geodesy.Unit` de comprimento. Alturas físicas ficam
em metros, independentemente do exagero vertical. Limites `set_xlim`, `set_ylim`
e `set_zlim` são físicos e crescentes; **não longitude/latitude**. Exagero atua
somente na transformação de exibição, sem alterar geometria, alturas ou colorbar.

`None`, NaN e valores mascarados de Z retiram as células adjacentes; não são
preenchidos com terreno inventado. Células degeneradas, formas incompatíveis,
malha vazia e valores não finitos de X/Y são rejeitados. Triângulos têm normais
orientadas para cima, inclusive com linhas Y decrescentes.

## DEM geográfico e referencial local

```python
from azimlib.raster import GeoRaster

dem = GeoRaster([[100, 110], [115, 130]],
                (.001, 0, -46, 0, -.001, -23), crs='EPSG:4326')
surface = ax.terrain(dem, origin=(-46, -23), elevation_unit='m',
                     elevation_reference='referência declarada pelo DEM')
```

Os centros dos pixels são transformados pelo CRS próprio para EPSG:4326 e para
Leste/Norte de um plano tangente local WGS84 na origem explícita. Affines com
rotação/cisalhamento são aceitas; transformação de CRS limita-se aos sistemas
que nosso núcleo já suporta. **Z continua sendo a altura fornecida**, sem
conversão silenciosa entre geóide, elipsóide ou datum vertical. A descrição de
`elevation_reference` é metadado do Artist, não uma transformação nem um aviso
de licença. A região deve estar até 250 km da origem. Não é um globo 3D; o
globo ortográfico 2D existente permanece separado.

Uma axes usa uma única `LocalFrame`; mudar a origem exige outra axes. Os limites
referem-se aos vértices utilizados da malha. A superfície amostra os centros dos
pixels, não reconstrói a cobertura das bordas; não há resampling implícito.

## Construções extrudadas

`ax.buildings(data, height='height', base='base', coordinates='geographic')`
usa plantas GeoJSON EPSG:4326 no mesmo referencial local do DEM. Height/base
podem ser números, propriedades ou funções de Feature; a unidade é `unit='m'`.
Base é a altitude física da base; height é a altura positiva acima dela. Não
estimamos automaticamente pavimentos, datum, base no terreno ou altura OSM.

`coordinates='world'` aceita um mapping tipo FeatureCollection com XY físicos;
ele não passa pelo parser angular de GeoJSON. Plantas simples, inclusive côncavas,
recebem teto, piso e paredes triangulados. IDs ficam em `artist.feature_ids`.
Holes, MultiPolygon, auto-interseções, vértices repetidos e plantas maiores que
256 vértices são rejeitados neste corte. Um lote inválido não é anexado parcialmente.
Não há picking 3D por construção, texturas ou reconstrução de cidades realista.

## Artists, câmera e interação

- `surface.set_visible(False)` e `remove()` usam o ciclo de vida da figura.
- `set_cmap`, `set_norm`, `set_clim` atualizam a colorbar pelo ScalarMappable.
  `set_array` recebe um valor por vértice e altera os escalares de cor, mantendo
  a elevação física; valores ausentes ocultam faces. A cor da face é a média dos
  seus três escalares. A colorbar mostra os valores anteriores à iluminação.
- `set_color` fixa uma cor; `set_shade(False)` desliga iluminação Lambert plana.
  O vetor de luz é expresso no mundo físico. Sem interpolação de normais/cores.
- `view_init(elev, azim, roll)`, `set_proj_type('ortho'/'persp', fov=35)` e
  `set_camera(terrain3d.Camera(...))` alteram a câmera própria. Zoom é magnificação,
  não caminhada pela cena. Eixos/ticks são decorações de tela, não geometria oclusora.
- Tk e Qt: Pan com botão esquerdo orbita; Pan com direito ou a ferramenta Zoom
  varia magnificação por arrasto vertical; roda aproxima/afasta. Zoom 3D não é a
  seleção retangular geográfica. Home/Voltar/Avançar restauram a câmera; não
  desfazem edições de dados, limites físicos ou exagero. Soltar/perder o botão
  encerra o gesto. Cursor não inventa lon/lat/XYZ a partir de uma imagem 3D.
- `browser-live` usa o controlador Python; HTML offline tem **snapshot estático
  do terreno**, sem órbita. Mapas 2D na mesma figura mantêm navegação geográfica.
  Notebook recebe o SVG com terreno embutido, sem widget 3D independente.

Frame, títulos, nomes dos eixos, colorbar e `grid(True/False)` são opcionais.
Grid não aparece por padrão. Formas 2D, annotations, legendas cartográficas,
escala, norte, rosa dos ventos e inset maps **não são adaptados automaticamente
para 3D**; use-os nas axes 2D ao lado. Não existe compatibilidade integral com
`mplot3d`, sharex/sharey 3D, escalas log 3D, eixos invertidos ou texto geográfico 3D.
API experimental: somente os métodos acima fazem parte deste contrato.

## Exportação e limites verificáveis

`savefig()` mantém figuras estáticas sem toolbar. PNG usa triângulos com clipping
nas seis faces homogêneas e depth buffer próprio. SVG embute PNG do terreno e
preserva os textos/eixos vetoriais; precisa de `azimlib[png]` para codificação.
PDF incorpora RGB comprimido e soft mask do terreno; eixos e contornos de texto
continuam vetoriais. Não prometemos terreno SVG/PDF vetorial, texto PDF pesquisável,
transparência de superfícies sobrepostas ou exportação de um modelo 3D.

Somente faces opacas ou inteiramente ocultas: alpha parcial é rejeitado. Empate
de profundidade em 1e-7 mantém a primeira face. Pixels são amostrados no centro;
PNG compõe em supersampling próprio, SVG/PDF usam a resolução da cena. Bordas
podem diferir pelo antialiasing; conteúdo geométrico, máscara e orientação são iguais.

Limites por axes: 50 mil vértices por malha e 20 mil triângulos no total; por
rasterização: 8 milhões de pixels e 64 milhões de testes de bbox. PNG conta os
pixels de supersampling (3× em cada dimensão); DPI alto pode exceder o budget.
São limites de CPU/memória, não precisão GIS nem garantia de FPS. Não há LOD
automático, GPU, volume/nebula, tiling de terreno ou memória nativa/RSS auditada.

Veja [galeria reproduzível](_static/terrain3d/README.md),
[contratos numéricos e de integração](../tests/test_terrain3d.py),
[benchmark](terrain3d-benchmark-0.3.json) e [checklist](release-progress-0.3.md).
Os resultados da etapa 7 permanecem snapshots do runtime anterior; não são
reescritos para fingir validação do runtime 3D. A **7.08 continua pendente**.
