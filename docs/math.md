# Matemática cartográfica e contrato de coordenadas

O núcleo implementa as fórmulas diretamente, com a biblioteca padrão do Python.
Não importa nem executa PROJ, pyproj, Shapely, Cartopy, GeoPandas ou Matplotlib.
As referências abaixo documentam os modelos matemáticos; não são dependências.

## Coordenadas e geometrias

Uma posição é `(longitude, latitude[, altitude])`, em graus decimais. A altitude
é preservada no intercâmbio e ignorada na visualização bidimensional. Números
não finitos, booleanos como coordenadas, latitudes fora de ±90°, linhas com um
só vértice e anéis sem fechamento explícito são rejeitados. Longitudes de
geometrias podem estar desenroladas para representar uma passagem pelo
antimeridiano. O módulo CRS exige a faixa convencional ±180°.

O leitor implementa os sete tipos de geometria do
[RFC 7946](https://www.rfc-editor.org/rfc/rfc7946.html), além de Feature e
FeatureCollection. Aceita geometria nula, coordenadas vazias, altitude e
polígonos com buracos. Retorna sempre uma FeatureCollection imutável. A ordem
dos eixos é explicitamente longitude/latitude, inclusive quando se usa o nome
EPSG:4326. Objetos GeoJSON com declaração antiga de CRS precisam de transformação
explícita. Membros estrangeiros não são preservados pelo leitor.

`bounds` é uma caixa cartesiana dos valores de longitude e latitude existentes;
não calcula o menor intervalo circular. Uma geometria que cruza ±180° pode ter
uma caixa muito larga. Use uma extensão cruzada explícita ou `ax.fit_extent()` nesse caso;
veja o [contrato de antimeridiano](geodesy.md).

## Projeções esféricas

O raio padrão é **6.371.008,8 m**. Cada projeção aceita coordenadas geográficas
em graus e produz metros; `inverse` desfaz a transformação. Coordenadas
geográficas inválidas geram ValueError. Um ponto válido fora do domínio finito
da projeção retorna None. Isso inclui o hemisfério oculto da Ortográfica.

Para longitude relativa ao meridiano central λ e latitude φ:

| Projeção | Modelo e observações |
|---|---|
| Equiretangular | x = R λ cos φ₁; y = R (φ − φ₀). Paralelo padrão configurável. |
| Mercator | x = R λ; y = R ln tan(π/4 + φ/2), com origem vertical ajustável. O limite padrão é ±85,0511287798066°. Latitudes externas são rejeitadas pelo domínio, sem deslocar pontos para o limite. |
| Equal Earth | Pseudocilíndrica equivalente; polinômio em θ = asin(√3 sin φ/2), com coeficientes 1,340264; −0,081106; 0,000893; 0,003796. A inversa resolve o polinômio por Newton. |
| Ortográfica | Projeção do hemisfério visível no plano tangente. A visibilidade é calculada pelo produto escalar com a direção do centro. |
| Lambert cônica conforme | Cone esférico com dois paralelos padrão, inclusive configuração no hemisfério sul. Preserva ângulos localmente. |
| Albers cônica equivalente | Cone esférico com dois paralelos padrão; preserva áreas do modelo esférico. |

As fórmulas clássicas são descritas por John P. Snyder em
[Map Projections—A Working Manual, USGS Professional Paper 1395](https://pubs.usgs.gov/publication/pp1395).
A [documentação oficial da Equal Earth no PROJ](https://proj.org/en/stable/operations/projections/eqearth.html)
registra o artigo de Šavrič, Patterson e Jenny e um ponto de referência na esfera
unitária, usado nos testes. As implementações deste projeto foram escritas
diretamente, sem vincular a biblioteca PROJ.

Os parâmetros `central_longitude` e `central_latitude` deslocam a origem; na
Ortográfica, ambos também orientam a câmera. Equiretangular aceita
`standard_parallel`; as duas cônicas aceitam `standard_parallels=(p1, p2)`.
Paralelos opostos, que degenerariam o cone, geram erro explícito. Uma projeção
pode ser estendida herdando Projection e usando `register_projection`.

## CRS e distâncias

CRS e Transformer implementam EPSG:4326, EPSG:3857 e WGS84 UTM
(EPSG:32601–32660 e 32701–32760), no domínio regional documentado em
[geodesia](geodesy.md). Web Mercator usa
**R = 6.378.137 m**, diferente do raio cartográfico padrão. Transformações de
datum e grades de deslocamento não estão implementadas. Geodesic fornece
operação elipsoidal explícita; as funções esféricas existentes são preservadas.
`transform_geojson` lê dados projetados antes de validar a geometria geográfica,
transforma posições e elimina caixas e metadados de CRS que ficariam obsoletos.

`haversine`, `destination` e `great_circle` operam na esfera. Distâncias não são
resultados geodésicos elipsoidais; a diferença pode ser material em levantamentos
de precisão. O círculo máximo usa interpolação vetorial esférica e rejeita
extremos exatamente antípodas, que não definem um arco único.

## Recorte para renderização

Linhas são divididas na costura do meridiano oposto ao centro da projeção. A
interpolação é linear em longitude/latitude, como os segmentos de GeoJSON.
Rotas de círculo máximo devem ser amostradas antes da divisão.

Polígonos usam recorte em faixas de longitude, retendo buracos no mesmo ramo
do exterior. Calotas polares previamente cortadas e fechadas explicitamente
ao longo do polo são suportadas, incluindo a Antártida dos dados incorporados.
Anéis polares sem esse corte não são aceitos pelo recorte em faixas. Polígonos
côncavos recortados podem conter conexões de largura zero, adequadas à regra
de preenchimento par-ímpar, sem promessa de topologia editável.

O recorte ortográfico amostra segmentos em até 2°, encontra interseções com o
horizonte e conecta trechos por arcos do limbo. O interior desses arcos é
verificado por um teste esférico de winding. Cada anel representa seu interior
menor que um hemisfério. Polígonos autointersectantes e interiores que cobrem
a maior parte da Terra não fazem parte do contrato. Isso é um recorte de
renderização aproximado; não é um motor geral de operações booleanas esféricas.

## Evidência de validação

Os testes verificam valores analíticos e de referência, ida e volta das projeções nos dois hemisférios, área diferencial de Equal Earth/Albers,
conformidade local de Lambert, pontos conhecidos de Web Mercator, validação de
GeoJSON, buracos, imutabilidade, costura e antípodas. Também recortam todos os
países incorporados em quatro vistas ortográficas, incluindo uma vista polar,
e verificam que os resultados estão fechados e dentro do disco projetado.
