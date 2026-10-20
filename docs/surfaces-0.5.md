# Fase B — superfícies planetárias, em desenvolvimento

Contrato de validação fixado antes da geração/avaliação das referências desta
fase. Fonte de entrada: Fase A `b991407f6efdb0c389f68e09025774889536fbab`.
Não é publicação nem certificação universal de superfícies ou efemérides.

## Tolerâncias prévias e domínio

- Projeções esféricas: erro XY absoluto <=1e-5 m no corpus independente.
- Projeções oblatadas EQC/Mercator/estereográfica polar/ortográfica: <=0,05 m.
- TM regional: <=0,5 m, longitude a até 3 graus do meridiano, latitude [-80,84].
- Inversas: <=1e-8 grau, excluídos pontos a menos de 1e-6 grau do horizonte
  tangente/singularidades; esses pontos são verificados por domínio/visibilidade.
- Geodésicas: distância <=0,05 m, azimutes <=1e-7 grau onde a solução é única;
  casos difíceis/antipodais têm budget de distância 0,1 m, sem exigir um azimute
  único onde há múltiplas soluções físicas.
- Áreas geodésicas: max(10 m², 1e-7 da área de referência), dentro do domínio
  declarado; área de retângulo lon/lat é outra operação, com bordas paralelas.
- Normais/incidência analíticas: erro absoluto <=1e-10; raster/perfis separam
  erro do modelo geométrico e erro de resolução/interpolação do dado.

O corpus cobre os cinco presets, polos, antimeridiano, pontos ocultos, regiões,
rotas curtas/longas e casos adversos. Os limites não prometem precisão para
todo Body arbitrário. Triaxial/irregular não recebem fallback esférico.

## Distinções obrigatórias

Distância geodésica na superfície, corda XYZ, distância no plano projetado e
caminho editorial são operações distintas. Altura radial/normal, datum/frame e
época vêm do PlanetaryContext; nenhuma orientação temporal é calculada aqui.
Rasters preservam unidades/proveniência, máscaras e NoData. Exagero vertical é
somente apresentação; não modifica os dados originais.

Iluminação geométrica recebe direção ou posição explicitamente no frame fixo.
Isso não calcula a posição astronômica do Sol, não pressupõe atmosfera e não
promove os eclipses experimentais. A iluminação/sombra do terreno ocorre antes
da câmera/exagero e reutiliza o renderer e a infraestrutura de sombras existentes.

Referências matemáticas: IOGP GN7-2/Snyder para projeções; geometria da quádrica
para normais/ortografia/terminador; Geodesic existente da Azimlib para esfera e
elipsoide de revolução. PROJ/GeographicLib/CSPICE são referências de QA, nunca
dependências de runtime nem implementações incorporadas.

## API funcional da Fase B

`BodySurface(context_or_body)` oferece `projection`, `inverse` (distância e
azimutes), `distance`, `direct`, `route`, `length`, `chord`, `polygon_area` e
`rectangle_area`. Distâncias usam metros por padrão, com Unit explícita nas
operações que recebem `unit`; azimutes são graus no sentido horário a partir
do norte geodético. Área retorna m². O mesmo objeto usa planetocêntrico ou
planetográfico conforme o contexto, convertendo para a latitude da normal
antes das fórmulas oblatadas. Contexto não calcula orientação temporal.

```python
import azimlib as azl
ctx = azl.PlanetaryContext.for_body(azl.MARS)
surface = azl.BodySurface(ctx)
print(surface.distance((20, 10), (22, 11), unit=azl.KILOMETRE))
projection = surface.projection('transverse_mercator', central_longitude=21)
fig, ax = azl.subplots(context=ctx, projection=projection)
ax.set_extent((19, 23, 8, 12))
ax.route([(20, 10), (22, 11)], color='red')
ax.scale_bar(length=20, units='km')
```

O preset Terra continua usando exatamente as projeções/defaults anteriores.
Para pedir a nova fórmula oblata na Terra, passe explicitamente
`BodySurface(ax.get_context()).projection(...)`. Fora da Terra, o padrão passa
da carta angular da Fase A para EQC métrica. `projection='angular'` preserva
a demonstração não métrica anterior; sua escala física continua recusada.
Imports raiz e pyplot, CPU padrão e propriedade única de Artists permanecem.

## Matriz de projeções e domínios

| Operação | Esfera | Elipsoide oblato (1/f >=150) |
|---|---|---|
| Equiretangular / EQC | Fórmula esférica | Longitude por ν(φts) cosφts; norte por arco meridiano |
| Mercator | Isométrica esférica | Isométrica elipsoidal; cap geodético padrão ±85,0511287798066° |
| Ortográfica | Disco e horizonte | Elipse exata; normal, visibilidade e inversa da quádrica |
| Estereográfica | Aspectos esféricos | Somente polar; latitude conforme e fator de escala |
| Transversa de Mercator | Implementação regional existente | Série oblata existente; ±3° de longitude, latitude geodética [-80,84] |
| Equal Earth, AEQD, LAEA | Implementadas | Recusadas, sem esfera substituta |
| Triaxial/irregular | Não se aplica | Operações de superfície recusadas; [investigação](surfaces-research-0.5.md) |

As inversas retornam contexto angular, não metros. Entradas gráficas requerem
graus leste/signed, offset meridiano zero; o renderer pode desenhar longitudes
desembrulhadas no antimeridiano. Os meridianos −180 e +180 são bordas distintas
da carta planificada, embora representem a mesma posição física. Geodesy aceita
as demais convenções explícitas do contexto. Não há conversão de Body/datum.
Mercator recorta na latitude correta da convenção ativa, não confunde latitude
planetocêntrica com geodética. Ortografia faz clipping de linhas/polígonos no
horizonte; curvas de desenho são amostradas pelo mecanismo existente de paths,
não um certificado de envelope contínuo para qualquer geometria arbitrária.

As áreas geodésicas esféricas usam polígonos simples com menor interior e
sem arestas antipodais. Nas oblatadas são suportados anéis simples sem
enrolamento polar, vértices |latitude geodética|<=80°, arestas dentro de 85°,
3–256 vértices. Furos, complementos e polígonos polares oblatos não são
implicitamente aproximados. `rectangle_area` integra paralelos/meridianos e
aceita calotas; não equivale a um polígono de arestas geodésicas.

## Raster, relevo e memória

`PlanetaryRaster` é um grid imutável: affine de **cantos** com seis
coeficientes, pixels em centros quando solicitados, PlanetaryContext,
BodySource, licença obrigatória e copyright separado. Resolução declara
unidades do grid (ângulos ou metros de SurfaceProjection); DEM usa Unit de
comprimento, intensidade usa `'1'`, imagem usa `'rgba'`.

`sample`, `crop`, `resample`, `mosaic`, `profile`, `hillshade` e `from_image`
são funcionais. Reamostragem inversa é nearest/bilinear; NoData pode ser
estrito ou renormalizado explicitamente; RGBA usa alpha premultiplicado.
Mosaico aceita até 16 fontes de mesmo contexto/unidades/modo, mantém as
proveniências e exige política de sobreposição. Licenças distintas exigem
composição externa explícita: não se apagam atribuições.

RasterBudget verifica **antes** da materialização: padrão 262.144 pixels e
64 MiB de estimativa conservadora de grid/entrada (160 bytes por célula),
limites configuráveis até quatro milhões de pixels e 1 GiB. Essa estimativa
não é um limite de RSS de todo o processo/renderização. A leitura local tem
limite de bytes e verifica SHA-256 quando declarado. Nenhuma rede/download.
Recorte é uma janela de pixels, sem materializar um mosaico inteiro.

`ax.raster(raster)` usa MeshCollection/ScalarImage já existentes. Grids
angulares e cilíndricos separáveis são desenhados diretamente; affine girada
ou outra projeção de origem exige `resample` explícito para grid angular.
Grids que cruzem a emenda devem ser divididos explicitamente; não há merge
global implícito nem leitor PDS/ISIS/GeoTIFF planetário completo nesta fase.
`from_image` recebe georreferência e contexto do chamador; nome de arquivo
não permite inferir datum. Rasters Earth/Marte/Lua incompatíveis são recusados
antes de anexar um Artist.

`profile` percorre uma geodésica física, preserva resolução/unidade/fonte e
expõe `distance_m`, `elevation_m` e, opcionalmente, `projected_distance_m`.
Mais amostras não aumentam a resolução real do DEM. Alturas e exagero visual
são separados. Os perfis de QA incluem NoData e bilinear; não certificam
acurácia de um DEM observado não fornecido.

`TerrainAxes.terrain(raster, origin=(lon,lat))` produz o SurfaceArtist/Mesh
existente, com SurfaceFrame ENU exato via XYZ, unidades em metros e raio local
limitado a min(250 km, 0,1 semieixo). Sem origin usa XYZ fixo do corpo. O dado
escalar continua sendo altura, não a coordenada Z global. Exagero vertical
local não altera mesh/dataset científico. XYZ global recusa exagero !=1,
pois não há um eixo vertical único. A malha global demonstrativa é grosseira,
em centros de pixels, com emenda/calotas abertas explicitadas; não é um sólido
fechado nem modelo global de terreno certificado.

Textura usa `SurfaceArtist.set_texture((width,height,rgba_bytes), uv=...)`,
com UV explícito por vértice, máscara binária e budgets existentes. 3D mantém
o status experimental do renderer anterior. PNG é raster; SVG/PDF preservam
vetores 2D quando possível e incorporam o tile 3D rasterizado, sem prometer
vetorização de superfícies 3D. Viewer HTML/browser recusa novas projeções
planetárias físicas enquanto o JavaScript não tiver o mesmo contrato; não
desenha silenciosamente com fórmulas terrestres. Exportação CPU e contexto
Python são o caminho demonstrado nesta fase.

## Luz: geométrica versus astronômica

`GeometricLight(context, direction=XYZ)` recebe direção unitária normalizada
para a fonte; `position=XYZ` recebe posição finita em metros no frame fixo,
fora do elipsoide. `normal`, `incidence` (cosseno assinado) e `terminator`
usam a quádrica real, incluindo o terminador de fonte finita. Sem clock.
Nas esferas normais são radiais; nas oblatadas são proporcionais a
`(x/a²,y/a²,z/c²)`, sem confundir radial e normal.

`ax3d.geometric_light(light, shadows=True, ...)` reutiliza iluminação/BVH e
ray tracing existentes em geometria científica, antes da câmera/exagero.
Suporta fonte direcional, sombras duras, ambient/diffuse explícitos e budgets
de refinamento/interseção. Fonte finita 3D, penumbra, sombras com texturas
mascaradas, atmosfera e espalhamento são recusados/não implementados; não
viram fonte distante ou atmosfera terrestre implicitamente. Iluminação de
terreno sem sombras pode usar textura. `hillshade` calcula normais dos
vizinhos físicos e declara o exagero usado; não é um modelo atmosférico.

`set_time` é recusado no GeometricTerrainLight. Os nomes IAU de frame não
calculam rotação temporal; não se inventam efemérides para outros corpos.
Sol/Lua/eclipses terrestres anteriores e seus status permanecem intactos.

## Referências independentes e reprodução

As fixtures usam chamadas black-box PROJ/GeographicLib/CSPICE, com versões,
entradas, convenções e saídas em `tests/fixtures/surfaces-050.json`. O gerador
não importa Azimlib; os testes do corpus não importam os oracles.
PROJ 9.8.1 usa y esférico em `eqc`; a comparação oblata usa arco meridiano
independente GeographicLib, conforme a definição de
[EQC elipsoidal EPSG:1028](https://proj.org/en/stable/operations/projections/eqc.html).
Não se troca a fórmula por aquela que produz menor erro. As origens são
normalizadas explicitamente, pois alguns métodos PROJ ignoram `lat_0`.
Normais independentes usam
[CSPICE surfnm](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/surfnm_c.html).
Nenhum código, kernel, texto de implementação ou asset desses projetos é
incorporado; os outputs são registros numéricos factuais de QA.

```sh
python -m unittest discover -s tests -p 'test*050.py' -v
python tools/validate_planetary_surfaces.py --output scientific-errors.json
python examples/planetary/surfaces_050.py --output surface-gallery
```

O índice local inclui PNG/SVG/PDF, contexto, dados, unidades e limitações.
Todas as elevações/imagens não terrestres demonstrativas são sintéticas
determinísticas, sob BSD-3-Clause; não são mapas NASA ou topografia medida.
O workflow dedicado `planetary-surfaces-0.5.yml` só executa `dev/0.5.0`, gera
evidências nos três sistemas e não tem permissão/etapa de publicação.
Resultados locais Windows não equivalem a execução nativa Linux/macOS.
Somente a validação da Fase B pode atualizar sua própria evidência; relatórios
da Fase A e quatro gates adiados da 0.4.0 continuam históricos e inalterados.
