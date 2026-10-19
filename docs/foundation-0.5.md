# Fundação 0.5.0 — Fase A em desenvolvimento

Escopo desta fase: Body público e presets, coordenadas estáticas, contexto em
Figure/MapAxes/Artists e grupos de Layers 2D. Os exemplos temáticos completos,
superfícies/projeções planetárias métricas, iluminação planetária e órbitas
continuam nas fases seguintes. Não são capacidades entregues por esta fundação.

## Contrato numérico fixado antes da validação

As conversões estáticas serão comparadas a fixtures analíticas e CSPICE
independentes: erro XYZ/altura absoluto <= **1e-7 m**, latitude/longitude
<= **1e-10 grau**, no corpus e domínio especificados. Essas tolerâncias são
numéricas para uma superfície ideal declarada, não precisão de uma observação
planetária ou certificação global de datum/efeméride/geodesia.

Esferas e elipsoides oblatos usam raio/eixos em metros. Planetográfico significa
latitude da normal e altura sobre a superfície de referência, não areoide/geóide.
O solver normal reutiliza `_frames.GeodeticFrame` e exige esfera ou inverso do
achatamento >=150; altura >= -min(10000 m, 1% do semieixo polar). Planetocêntrico
significa direção radial e altura radial: para direção unitária u, a superfície
é r = 1 / hypot(u.x/a, u.y/b, u.z/c). Esse contrato também permite conversão
radial em triaxial, sem oferecer geodésicas/áreas ou inversa planetográfica
triaxial. O centro é indefinido e recusado. Semieixos aceitos: 1e-3 a 1e12 m.

Longitude é lida segundo direção/intervalo explícitos e convertida para o eixo
X de referência por um offset do meridiano principal em graus leste. O domínio
signed aceita [-180,180] e normaliza a saída a [-180,180); positive usa [0,360)
na saída. Polos têm longitude matematicamente indeterminada: a validação não
exige preservação de longitude no polo. Unidades de ângulo e altura usam Unit.

Datum, frame, época e orientação são identificadores estáticos. Igualdade de
frame inclui época. `convert` recusa troca de Body/datum/frame/época; nenhum
identificador executa rotação IAU, transformação inercial ou cálculo temporal.
Malhas irregulares têm representação explícita de triângulos com proveniência,
mas interseção radial/normal, projeção de superfície e geodésia são recusadas.
As validações da malha não certificam fechamento, orientação ou topologia global.
Vértices irregulares são limitados a magnitude absoluta de 1e12 m por componente,
evitando overflow na validação local de triângulos; não é um certificado de malha.

## Presets e origem dos parâmetros

Terra preserva o Ellipsoid WGS84 existente e os defaults da 0.4.0. Lua e Vênus
usam esferas; Marte e Mercúrio usam eixos oblatos. Fonte dos quatro presets:
[NASA NAIF pck00011](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc),
edição 2022-12-27, SHA-256
`3dff7b1dbeceaa01f25467767d3fa25816051c85d162d1edf04acb310ee28bb1`.
São constantes factuais convertidas de km para m, com origem preservada no
BodySource; nenhum kernel, código CSPICE ou texto de implementação é incorporado.
Não há download em import, construção, conversão ou renderização.

Os nomes de frames IAU dos presets são declarações de contexto, não um serviço
de orientação temporal. Convenções gráficas padrão são leste/signed explícitas;
não são inferidas da rotação prógrada/retrógrada de cada astro. O preset não
seleciona uma realização de datum ou efeméride de missão.

## API pública e contexto

`Body`, `BodySource`, `SurfaceMesh`, `BodyRegistry`, `BODIES`, `EARTH`, `MOON`,
`MARS`, `VENUS`, `MERCURY`, `LongitudeConvention`, `PlanetaryContext`,
`PlanetaryData`, `Capability`, `CapabilityStatus`, `UnsupportedBodyOperation`
e `ArtistGroup` são públicos de desenvolvimento. Body e seus metadados são
imutáveis. `Body(name, Ellipsoid)` continua disponível para o código anterior.
BodyRegistry é local/imutável; `with_body` produz outro registro, sem alterar
o global. Não há registro remoto ou substituição silenciosa de IDs.

`ReferenceFrame`, `Coordinates`, `RigidTransform` e `GeodeticFrame` expõem a
mesma fundação estática de `_frames`, sem duplicar implementações. Esses nomes
não acrescentam transformações inerciais ou orientação temporal.

```python
import azimlib as azl

context = azl.PlanetaryContext.for_body(azl.MARS)
xyz = context.to_fixed(0, 0, 0)
assert xyz.xyz == (3396190.0, 0.0, 0.0)
assert context.from_fixed(xyz) == (0.0, 0.0, 0.0)

fig = azl.figure(body=azl.MARS)
ax = fig.add_subplot(111)
ax.plot([0, 20], [0, 10])
assert ax.get_body() is azl.MARS
fig.close()
```

Figure fornece contexto padrão; add_axes/add_subplot e subplot_kw podem
declarar outro Body/contexto. MapAxes o preserva em seus Artists, decorações,
insets e metadados da Scene. O contexto é somente leitura; não se muda o Body
de um Axes que já possui dados. Corpos diferentes podem coexistir na Figure,
mas não compartilhar eixos nem receber o mesmo Artist mutável.

Os números passados a plot/scatter/text/polygon pertencem ao contexto do Axes.
Dados geográficos externos não terrestres exigem PlanetaryData ou context
explicitamente informado; o leitor GeoJSON puro mantém sua semântica terrestre.
`read_geojson(source, context=...)` é uma declaração explícita sobre as
coordenadas de origem e retorna o wrapper, não uma redefinição do RFC 7946.
Contextos incompatíveis são recusados antes de attach/fit; não são descartados
implicitamente por leitura, estilização ou reutilização.

## Renderização desta fase

Mapas da Terra preservam o renderer e as projeções existentes. Outros Bodies
usam somente **cartas angulares não métricas**, equirectangular radius=1,
planetocêntricas, graus leste/signed e meridiano zero. Isso permite inspecionar
contexto, geometria angular, estilo, grupos e exportação, sem simular uma
projeção física oblatada/esférica certificada. Scene declara `metric_surface=false`.
Não confundir o tamanho visual da carta com o tamanho físico do Body.

Axes terrestres continuam aceitando apenas latitude geodética, graus leste
signed e meridiano zero. Contextos diferentes podem ser usados na conversão
estática, mas precisam ser convertidos explicitamente antes de desenhar.
`subplot_mosaic` não generaliza projeções para outros Bodies nesta fase;
use Figure/add_subplot ou subplots com subplot_kw. O terrain Axes 3D
permanece terrestre e exige Body Terra explicitamente em uma Figure planetária.

Escala métrica, datasets terrestres, overview terrestre, geodésicas de superfície,
raster/terreno e modelos Sol/Lua da Terra em Axes planetário são recusados.
Rotas editoriais com `geodesic=False` permanecem linhas angulares explícitas.
PNG/SVG/PDF CPU e canvas estão disponíveis no recorte; GPU com contexto
planetário ou grupos é recusado nesta fase, sem alterar o backend GPU existente.
Não há garantia nova de latência. Não se acrescenta dependência obrigatória.

## Grupos e ownership

`ax.group(name=..., parent=..., style=..., zorder=..., visible=..., clip_on=...)`
cria grupo de Layers 2D pertencente a um único Axes. `add`, `discard`, `remove`,
`get_children`, `set_visible`, `set_zorder`, `set_style` e `instantiate` exercitam
contratos reais, sem um segundo renderizador. O renderer continua a lista plana
de Layers; findobj/ownership usam a hierarquia, sem contar folhas duas vezes.

- Visibilidade efetiva = visibilidade local AND todos os ancestrais; ocultar
  grupo não apaga a decisão local. `get_local_visible` expõe essa decisão.
- Estilo: grupo ancestral → grupo mais próximo → propriedade local do Artist.
  Defaults existentes explícitos do Artist continuam ganhando. Estilos só
  contêm propriedades visuais allowlisted, nunca geometria/contexto/datasets.
- Zorder é a ordem local mais os offsets dos grupos. Não implica composição
  isolada/atômica de um grupo inteiro ou modo de blending novo.
- Clipping de grupo pode forçar o retângulo do Axes já existente. Clipping
  geográfico/poligonal comum permanece futuro; não é uma máscara científica.
- Picking reporta a folha original; callbacks e stale propagam pela árvore.
  Mudanças no grupo também invalidam os seriais usados nos caches das folhas.
- Transformação de descendentes ou picking agregado pelo grupo não estão
  implementados; set_transform/set_picker no grupo recusam a operação. Configure
  esses controles nas folhas. Transforms geográficos conhecidos também recusam
  contextos incompatíveis, inclusive dentro de uma mesma Figure; transforms
  físicos/afins/fracionários continuam separados da semântica geográfica.
- Não há ciclos, dois grupos para uma folha ou attach a outro Axes. Remover
  grupo remove/detacha descendentes; clear/remove do Axes limpa os grupos.
- `instantiate` suporta somente grupos de Layers geométricos simples imutáveis,
  sem callback de estilo, mapping ou transform customizado; cria novos handles,
  estilos/estado/callbacks independentes e compartilha apenas o dado imutável.
  Clonagem de raster/texto/coleções especializadas é recusada até contrato próprio.

## Pontos de extensão, sem funcionalidades editoriais antecipadas

| Responsabilidade | Fundação efetiva / extensão futura |
|---|---|
| Dado/geometria | FeatureCollection imutável + PlanetaryData; temas/grupos não alteram coordenadas |
| Coordenada/transformação | PlanetaryContext estático; futuros projetores usam o Body e recusas explícitas |
| Aparência | Styles existentes/defaults de grupo; símbolos/padrões/curvas continuarão Artists |
| Instância visual | Uma folha por Axes; instantiate delimitado, sem copiar callbacks ou viewport |
| Composição | Figure/Axes/insets/layout existentes; locator e legendas seccionais continuam futuros |
| Texto/exportação | Shaping/paths/backends existentes; sem antecipar labels/editorial completos |

Importação SVG já possui subconjunto local limitado em `icons.py`: uma path,
sem scripts, URLs, imagens/fontes embutidas ou carregamento externo, com
proveniência/hash. A fase A não amplia esse parser nem anuncia SVG arbitrário.
Uma curva editorial futura deve guardar seu dado original e seu espaço visual;
nenhuma API vazia foi criada para simbolizar essa funcionalidade futura.

`Body.capability(operation, backend=...)` distingue supported, experimental,
research e not_implemented. O resultado não é um solver: `require` recusa o
que não é suportado, salvo experimental explicitamente permitido. Distingue
coordenadas radiais/normais, carta angular, projeções/geodésia, orientação
temporal e geodésia irregular. Backend GPU não recebe validação por analogia.

| Modelo / presets | XYZ radial estático | Normal/planetográfico | Carta angular CPU | Superfície planetária métrica / orientação temporal nova |
|---|---|---|---|---|
| Esfera: Lua/Vênus | Suportado | Suportado no domínio raso/exterior | Experimental | Não implementado |
| Oblato: Terra/Marte/Mercúrio | Suportado | Suportado no domínio/achatamento declarados | Experimental fora da Terra; Terra preserva mapas existentes | Novo contrato planetário não implementado; APIs terrestres anteriores preservadas |
| Triaxial fornecido | Suportado radialmente | Recusado | Experimental | Não implementado |
| Malha irregular fornecida | Recusado | Recusado | Recusado | Geodésia em pesquisa; demais operações não implementadas |

As consultas de capacidade cobrem os contratos novos desta fundação, não são
um inventário completo das APIs terrestres legadas. Grupos são organização de
Layers de um Axes 2D existente, não prova de suporte à superfície desse Body.
SVG/PDF mantêm os backends existentes; PNG depende do extra anterior. O estado
geométrico da capacidade não instala nem certifica disponibilidade de opcionais.

0.4.0 e seus quatro gates adiados permanecem intactos. A próxima fase é
Superfícies Planetárias (B), não órbitas ou certificação global de eclipses.
