# Progresso da Azimlib 0.3.0

Status: **em desenvolvimento, não publicada**. A versão estável publicada é 0.2.0.
Esta é a checklist operacional única; os IDs são estáveis. O [registro da 0.2.0](release-progress.md) permanece separado.

**78 concluídos / 2 pendentes**. Contagem por subpassos, não por frentes amplas.

## Regras de conclusão

Marcar um subpasso somente após implementação, testes de contrato/regressão e documentação.
Recursos visuais exigem exemplo reproduzível e exportação inspecionada. Novos formatos/datasets
exigem proveniência/licença, limites declarados e testes de dados inválidos. A conclusão do
passo exige integração entre seus subpassos; não basta uma API vazia ou um screenshot.
O estado de Python/plataformas só será atualizado a partir da CI efetivamente executada.
Matplotlib pode ser uma referência de comportamento em ferramentas de comparação; o runtime
continua independente e os componentes cartográficos permanecem opcionais.

O escopo é o corte verificável descrito abaixo, não a promessa de implementar todos os
toolkits/CRS/formatos do mercado. API 3D será experimental e própria. Mudanças de escopo
devem ser registradas aqui, com motivo, sem apagar IDs nem reduzir silenciosamente o total.

## Ordem dos lotes

Começar por 1; seguir com 2 e 3. O núcleo do passo 4 sustenta 5–9.
Acabamento/performance/licenças entram em cada lote; o passo 10 consolida os gates.
A numeração não impede corrigir uma regressão imediatamente.

## 1. Dados e fundação urbana

- [x] **1.01** Seleção imutável por atributos, predicado e tipo de geometria, preservando IDs/ordem.
- [x] **1.02** Leitor CSV de pontos com colunas/conversores explícitos e validação de registros.
- [x] **1.03** Artist de cidades/POIs, distinguindo centros de limites administrativos.
- [x] **1.04** Camada de bairros com filtros e estilos por feature.
- [x] **1.05** Camada de ruas com seleção de hierarquia e estilos físicos em pontos.
- [x] **1.06** Camada de plantas de construções, sem fingir extrusão 3D.
- [x] **1.07** Atlas urbano sintético exportável em PNG/SVG, usando somente o núcleo próprio.
- [x] **1.08** Contratos urbanos, erros sem mutação, ciclo de visibilidade/edição e testes de regressão.

## 2. Formatos, dados reais e proveniência

- [x] **2.01** Leitor Shapefile próprio: cabeçalho, índice SHX, Point/Polyline/Polygon e multipartes.
- [x] **2.02** Leitor DBF próprio, codificação explícita, registros excluídos e vínculo com SHP.
- [x] **2.03** Leitor KML próprio: placemarks, geometrias, altitude e política XML sem recursos externos.
- [x] **2.04** Leitor OSM XML local: nodes/ways e relações multipolygon, com diagnóstico de referências incompletas.
- [x] **2.05** Contrato de raster georreferenciado com extent/CRS/NoData e sidecars world-file.
- [x] **2.06** Entrada GeoTIFF inicial: tags de georreferência e variantes suportadas explicitamente delimitadas.
- [x] **2.07** Exemplo urbano real pequeno com fonte/versão/licença/atribuição e licença de dados separada.
- [x] **2.08** Catálogo de dados opcionais versionados, sem downloads implícitos, com validação de integridade.

## 3. CRS, geodesia e robustez cartográfica

- [x] **3.01** Modelo de elipsoide, parâmetros de datum e unidades com contratos públicos.
- [x] **3.02** Geodesia elipsoidal direta/inversa com convergência e casos quase antipodais verificados.
- [x] **3.03** Transversa de Mercator/UTM próprias, zonas/hemisférios e transformações inversas.
- [x] **3.04** Projeções adicionais prioritárias: estereográfica e azimutal equidistante.
- [x] **3.05** Viewport atravessando antimeridiano, incluindo navegação, ajuste de limites e exportação.
- [x] **3.06** Recorte esférico de linhas/polígonos com horizonte e casos degenerados documentados.
- [x] **3.07** Topologia básica: testes de interseção, orientação e validação de anéis/fronteiras.
- [x] **3.08** Matriz numérica de forward/inverse, singularidades, tolerâncias e dados em CRS explícito.

## 4. Transforms, Artists, escalas e composição

- [x] **4.01** Transforms composáveis geo/projetado/axes/figure/display com inversas e unidades físicas.
- [x] **4.02** Transforms mistos e vínculo de objetos existentes sem quebrar coordenadas geográficas.
- [x] **4.03** Linhas com gaps NaN/máscaras, Paths públicos e coleções editáveis em lotes.
- [x] **4.04** Locators/formatters de datas e logs; contrato de escalas separado de CRS/latitude.
- [x] **4.05** Ticks de graticules em bordas curvas e offsets científicos consistentes.
- [x] **4.06** SubFigure e solver para múltiplos GridSpecs raiz, preservando posições explícitas.
- [x] **4.07** Layout compressed, obstáculos de textos livres/cax e critérios de convergência.
- [x] **4.08** Ciclos de estilo nas demais famílias, símbolos reutilizáveis e handlers de legenda personalizados.

## 5. Raster, terreno e mapas científicos 2D

- [x] **5.01** Raster RGB/RGBA, máscaras/NoData e exportação consistente.
- [x] **5.02** Resampling nearest/bilinear de campos geográficos com cobertura e NoData.
- [x] **5.03** contourf próprio, níveis discretos, holes e ligação a ScalarMappable/colorbar.
- [x] **5.04** Campos irregulares e triangulação inicial própria com degenerações explícitas.
- [x] **5.05** Heatmaps/densidade, normalização, amostras ponderadas e controles de resolução.
- [x] **5.06** Fluxos/vetores geográficos e rotas geodésicas com legendas temáticas.
- [x] **5.07** Hipsometria/hillshade/topográfico: composição raster + contornos + hidrografia.
- [x] **5.08** Colorbars/legendas: máscaras, atualização de classes, norm/RGBA e edição vinculada.

## 6. Acabamento visual, texto e exportação

- [x] **6.01** Curvas/caps/junções e clipping fracionário: testes PNG/SVG no mesmo DPI.
- [x] **6.02** Tipografia subpixel e métricas/hinting, com auditoria de todos os tipos de texto.
- [x] **6.03** Âncoras interiores de polígonos, prioridade e colisões de labels/leader lines.
- [x] **6.04** Textos ao longo de curvas e repetição de nomes em ruas/rios extensos.
- [x] **6.05** Expressões matemáticas simples próprias e documentação das limitações de shaping.
- [x] **6.06** Símbolos/ícones externos e padrões customizados com proveniência explícita.
- [x] **6.07** Exportador PDF vetorial próprio, incluindo transparência e estratégia de fontes/avisos.
- [x] **6.08** Galeria comparativa de mapas completos e componentes, sem copiar assets/implementação de referência.

## 7. Interação, integração e desempenho

- [x] **7.01** Picking de features e seleção com tolerância em pixels e callbacks.
- [x] **7.02** Seletores, controle de camadas e sliders próprios, sem componentes obrigatórios.
- [x] **7.03** Ponte viva Python/viewer portátil para atualização/reprojeção em todas as projeções suportadas.
- [x] **7.04** Integração notebook com lifecycle/event loop e atualização de Figures.
- [x] **7.05** Backend Qt opcional próprio usando o mesmo canvas/renderer e comandos de navegação.
- [x] **7.06** Simplificação por erro em pixels, compartilhamento de fronteiras e caches incrementais.
- [x] **7.07** Benchmarks urbanos/densos: primeira pintura, pan, labels, memória e exportação.
- [ ] **7.08** Validação nativa Tk/Qt por plataforma e manutenção da fluidez/espessura física de linhas.

## 8. Terreno 3D experimental verdadeiro

- [x] **8.01** Contrato de coordenadas de elevação/unidades; separar altura física de exagero vertical.
- [x] **8.02** Câmera própria ortográfica/perspectiva e transforms mundo/view/clip/display.
- [x] **8.03** Clipping 3D, raster de triângulos e depth buffer próprios, incluindo oclusão.
- [x] **8.04** Artist de superfície/terreno com cores/norm, iluminação e máscaras.
- [x] **8.05** Extrusão inicial de plantas de construções com altitude/base explícitas.
- [x] **8.06** Órbita/zoom da câmera e reset, mantendo separada a navegação de mapas 2D.
- [x] **8.07** PNG 3D e política explícita para exportação SVG/PDF com camada raster.
- [x] **8.08** Galeria, testes de câmera/profundidade e limites de desempenho da API experimental.

## 9. Mapas temporais e atlas

- [x] **9.01** Modelo de frames e dados temporais, unidades/datas e seleção de instante.
- [x] **9.02** Artist/scene updates por frame, preservando mapa e componentes estáticos.
- [x] **9.03** Playback, pausa, slider, intervalo e encerramento de timers sem recursos pendurados.
- [x] **9.04** Escalas de cores/legendas globais ou por frame com comportamento explícito.
- [x] **9.05** Exportação de sequência PNG e GIF via dependência genérica opcional.
- [x] **9.06** Protocolo de encoder de vídeo opcional com dependências/erros documentados.
- [x] **9.07** Atlas por páginas e séries regionais com vistas/estilos compartilhados.
- [x] **9.08** Exemplos temporal/populacional/climático sintéticos e testes de repetibilidade.

## 10. Documentação, compatibilidade e entrega

- [x] **10.01** Documentação versionada/hospedada e guias de migração Matplotlib → Azimlib.
- [x] **10.02** Galeria política/física/urbana/científica/3D/temporal com scripts e proveniência.
- [x] **10.03** Contrato de compatibilidade/semver, API experimental e changelog completo.
- [x] **10.04** Auditoria de licenças/proveniência/privacidade de todas as novas fontes e assets.
- [x] **10.05** CI completa nos sistemas/Pythons suportados, incluindo novos readers e backends opcionais.
- [x] **10.06** Baselines visuais/numericamente verificáveis e gates de desempenho reproduzíveis.
- [x] **10.07** Atualizar versão/metadata, reconstruir wheel/sdist e testar instalação isolada/imports.
- [ ] **10.08** Aceite final e publicação 0.3.0 somente após gates; nenhuma publicação automática deste desenvolvimento.

## Evidências por lote

Nenhum subpasso é declarado concluído apenas por constar no plano. Evidências dos lotes
executados serão acrescentadas abaixo com arquivos, testes e limitações.

### Lote 1 — dados e camadas urbanas (0.3.0.dev0)

**1.01–1.08 concluídos.** Código em `geometry.py`, `tabular.py`, `io.py` e
`axes.py`; documentação no [guia urbano](urban.md); script em
[examples/urban.py](../examples/urban.py). Os dados do atlas são inteiramente
sintéticos. A [imagem e seu manifest](_static/urban/README.md) foram inspecionados
em PNG/SVG com o renderer próprio; nenhum motor cartográfico externo foi usado.

- [27 testes de contrato](../tests/test_urban.py): CSV/erros/conversores,
  igualdade de propriedades JSON, seleção preservando features/IDs/ordem,
  geometria errada sem mutação, multipartes, CRS explícito, aliases, styles por
  feature, edição/visibilidade/remoção e exportação.
- Suíte geral em código-fonte: 708 testes, sem falhas, dois skips Numba.
  Um teste adicional de seleção JSON composta passou no lote final de 27.
- [Relatório do wheel instalado](urban-validation-0.3.json): 709 testes,
  16.820 subtests, sem falhas/erros, com skips opcionais nomeados. Runtime
  verificado por hash contra o código-fonte. Ambiente local Windows/CPython
  3.14.4 com Pillow/NumPy, sem aggdraw/Numba; bibliotecas de referência/GIS
  não importadas. Isto não é uma CI nova de três plataformas.
- Wheel de desenvolvimento instalado também em ambiente limpo sem extras:
  core/GeoJSON/CSV/urbano/SVG e os dois estilos de importação aprovados pelo
  [smoke instalado](../tools/smoke_installed_package.py). PNG não é exigido
  no core sem Pillow.
- Auditorias locais de licenças/proveniência, privacidade e links aprovadas.
  [Validador da checklist](../tools/check_release_progress_030.py) integra a CI.
  A auditoria da distribuição confere BSD/composição de licenças, RECORD,
  conteúdo exato do wheel/sdist e exclusão de motores externos.

Leitores adicionais, bases urbanas reais, picking, largura em metros, extrusão
3D e roteamento não foram declarados implementados por este lote. O passo 1
encerra a fundação descrita; não encerra a frente urbana inteira. Ao final daquele lote, os passos
2–10 ainda estavam pendentes; o lote seguinte está registrado abaixo. Versão de desenvolvimento apenas local, sem PyPI.

### Lote 2 — formatos, dados reais e proveniência (0.3.0.dev0)

**2.01–2.08 concluídos no corte delimitado.** Implementação independente em
`shapefile.py`, `xmlio.py`, `raster.py`, `catalog.py` e `_readers.py`, integrada
em `azimlib`, `azimlib.io` e `MapAxes.raster`. O [guia de formatos](formats.md)
declara variantes, CRS, geometrias, entradas rejeitadas e limites de tamanho;
o [guia de dados opcionais](optional-data.md) descreve catálogo e atribuição.

- [32 testes novos](../tests/test_formats.py), com fixtures binários/XML próprios:
  SHX/DBF excluído e alinhamento físico, Point/Polyline/Polygon/multipartes/Z,
  KML/altitude/XML seguro, OSM multipolygon/furos/referências, affine/NoData,
  PixelIsArea/Point, endian/float/16-bit/deflate/matrix, hashes/licença,
  versões, path traversal e despacho integrado de todos os formatos.
- [Suíte completa do wheel instalado](formats-validation-0.3.json): **741 testes,
  16.879 subtests, zero falhas/erros**. Cinco skips opcionais/da plataforma são
  identificados no relatório, incluindo symlink sem permissão no Windows.
  Hashes de todos os módulos instalados conferidos contra o código-fonte.
  Sem imports de Matplotlib ou motores GIS. Evidência Windows local, não nova CI remota.
- Shapefile externo Natural Earth `ne_110m_populated_places` lido com SHX/DBF:
  243 pontos; arquivo real não vendorizado. Os readers vieram das especificações
  primárias listadas no guia, não de código de outro leitor.
- Exemplo [urbano real](../examples/urban_real.py): 464 ways, 3.876 nodes,
  extração OSM congelada de São Paulo em diretório opcional separado. ODbL,
  copyright/atribuição, texto integral da licença e proveniência preservados;
  metadados de editores e contatos/endereços removidos. PNG/SVG exportados e
  inspecionados com crédito visível. [Raster sintético](../examples/georaster.py)
  também inspecionado em PNG/SVG com colorbar editável e componentes opcionais.
- `tools/audit_optional_data.py` verifica quatro arquivos por hash e valida
  geometria/referências, tags permitidas e licença, sem rede. Gate incluído na CI.
  Catálogo tem versão explícita e verifica os bytes de dados, sidecars e avisos
  antes de interpretar. Nenhum import ou carregamento faz download.
- Wheel/sdist de desenvolvimento: dados ODbL excluídos explicitamente e por
  auditoria de distribuição; oito avisos legais do runtime preservados, BSD e
  licenças próprias de recursos anteriores mantidas. Smoke instalado sem extras
  cobre KML/OSM, GeoRaster/world-file/SVG e ambos os imports.

Este lote não implementa leitor universal, OSM PBF, CRS além de 4326/3857,
reparo topológico, raster RGB, resampling ou desenho de affines rotacionadas.
Esses limites aparecem na API/documentação; não são simulados nem delegados a
outro motor. Os próximos passos mantêm os IDs e o total de 80. Nenhum upload,
push ou alteração da versão estável 0.2.0 foi feito por este lote.

### Lote 3 — CRS, geodesia e robustez cartográfica (0.3.0.dev0)

**3.01–3.08 concluídos no corte regional explicitamente documentado.**
Implementação própria em `geodesy.py`, `transverse.py`, `topology.py`, integrada
em CRS, projeções, readers, rotas, viewport, cache, renderização e navegação.
O [guia do núcleo](geodesy.md) descreve modelos, erros, tolerâncias, entrada
explícita e limites. Funções esféricas anteriores foram preservadas.

- Elipsoide/datum/unidades imutáveis; WGS84/GRS80/esfera; geodesia elipsoidal
  direta/inversa com diagnóstico, solução própria por shooting multistart para
  falhas de convergência e sem fallback de distância esférica.
- UTM WGS84: 60 zonas, dois hemisférios, exceções de seleção Norway/Svalbard,
  forward/inverse e elevação preservada. TM elipsoidal regional ±6°; origem,
  escala e offsets explícitos. CRS/units/datum/axis order consultáveis.
- Estereográfica e azimutal equidistante esféricas, inversas, polos e antípoda
  singular. Novas projeções usam o mesmo renderer/cache/API próprios.
- Extensão cilindrica cruzada recenteriza cópia da projeção; limites crescentes
  desenrolados, fit circular optativo, pan/zoom, histórico/Home, shared x,
  exportação e modelo HTML portátil. LongitudeFormatter identifica E/W no ramo.
- Linhas ortográficas terminam no horizonte por bisseção. Testes de clipping
  de polígonos verificam limbo, inversão de winding e área degenerada; o recorte
  esférico com holes existente continua integrado. Não é overlay global.
- Topologia regional optativa O(n²): determinante com fallback racional,
  interseções ponto/overlap, anéis, holes e multipolígonos. Sem reparo automático
  nem alteração da permissividade dos datasets/geometrias existentes.
- [23 testes novos](../tests/test_geodesy.py) e [579 casos numéricos calculados](geodesy-reference-0.3.json),
  com [erros máximos/exports por hash](geodesy-numeric-0.3.json). Oráculos isolados
  pyproj 3.8.0/GeographicLib 2.1 apenas por chamadas black-box, sem código/test
  datasets vendorizados ou imports GIS em runtime/testes.
- [Suíte completa do wheel instalado](geodesy-validation-0.3.json): **764 testes,
  17.477 subtests, zero falhas/erros**; cinco skips opcionais/plataforma explícitos.
  Todos os módulos Python instalados conferidos por hash contra o código-fonte.
  Evidência Windows local/Python 3.14; não representa nova CI remota.
- Atlas [geodesy_atlas.py](../examples/geodesy_atlas.py) e mapa cruzado
  [pacific.py](../examples/pacific.py): PNG/SVG/HTML exportados, imagens inspecionadas,
  Natural Earth creditado, rotas sintéticas. savefig continua PNG/SVG sem UI;
  HTML usa to_html/show. Componentes continuam opcionais.
- Wheel/sdist, twine strict, oito avisos legais, integridade de dados/fontes/
  ícones, docs/snippets, smoke novo offline sem extras e dois smokes Tk ocultos
  de pan/viewer aprovados. Fontes/dados/paletas/ícones de terceiros preservados;
  nenhuma biblioteca GIS passou a ser backend/dependência. Varredura de privacidade
  e integridade Git integra o fechamento local deste lote.

Limites: datum shifts/epochs/grids e CRS universais não implementados; TM não
é global; novas azimutais são esféricas. Raster UTM é representável e lido, mas
plotting curvilíneo é rejeitado até seu lote. Topologia é planar lon/lat regional;
recorte esférico não aceita todos os interiores globais/degenerações. Autoscala
Cartesian legada continua; fit circular é opt-in. Reprojeção portátil viva nas
projeções não cilíndricas permanece no passo 7. Nenhum push/upload/publicação
ou modificação de main/0.2.0 foi feito. Checklist: **24/80**, **56 pendentes**.

## Corte explicitamente reservado à 0.4.0

| Recurso | Razão técnica | O que a 0.3.0 entrega antes |
| --- | --- | --- |
| Volumes 3D, nuvens volumétricas e GPU | Exigem pipeline volumétrico/paralelo além de superfícies e depth buffer | Câmera, terreno e extrusão experimental CPU |
| OSM PBF completo e planet-scale streaming | Codec binário, referências em blocos e consumo limitado de memória precisam de validação própria | OSM XML local validado e benchmarks urbanos |
| CRS universais e datum por grids oficiais | Catálogo, grids licenciados, inversão e tolerâncias são uma fundação adicional | Elipsoide, UTM e CRS/projeções explicitamente suportados |
| Overlay/union globais de topologia arbitrária | Robustez numérica/topológica global não pode ser inferida de clipping | Validação/interseções básicas e recorte esférico delimitado |
| Geocodificação e roteamento urbano completos | Dependem de índices de endereços, grafos/restrições de trânsito e licenças de bases reais | Leitores/camadas urbanas, seleção e picking |
| TeX completo e shaping internacional complexo | Requerem motor de composição e fontes/cobertura adicionais auditados | Tipografia/labels aprimorados e expressões simples próprias |

Estas reservas não substituem urbano, 3D e tempo: os três estão no corte 0.3.0.
Não há data prometida; 80 subpassos representam trabalho substancial. Novas funções
só serão anunciadas como disponíveis quando passarem pelos respectivos gates.

### Lote 4 — transforms, Artists, escalas e composição (0.3.0.dev0)

**4.01–4.08 concluídos no corte documentado.** Implementações próprias em
`transforms.py`, `path.py`, `patches.py`, `collections.py`, `dates.py`,
`scale.py`, `subfigure.py`, `legend_handler.py`, viewport/render/layout.
Veja [contratos e limites](transforms-composition.md) e a
[recomendação de visualização clara](visual-style.md).

- [27 testes de integração](../tests/test_transforms_composition.py): inversas,
  DPI/unidades, transforms mistos/insets/ownership, gaps/máscaras, paths/holes,
  edição atômica de coleções, datas/logs, bordas curvas/offsets, SubFigure,
  rollback entre raízes, compressed, obstáculos e handlers/ciclos.
- [Wheel instalado](composition-validation-0.3.json): **791 testes / 17.499
  subtests**, zero falhas/erros. Cinco skips explicitados: dois Numba, dois
  aggdraw e um symlink sem permissão. Hashes dos módulos do runtime conferidos
  contra o código-fonte final. Windows/CPython 3.14.4, Pillow/NumPy; nenhuma
  importação de Matplotlib/Cartopy/GeoPandas/Shapely/pyproj. Resultado local,
  sem atualizar o aceite de CI/plataformas da release.
- [Desktop instalado](composition-desktop-0.3.json): três smokes reais de Tk
  em janelas ocultas e input sintético — pan/lifecycle, viewer e nova composição
  com bearing/norte/rosa/history. Não é aceite visual/input humano. O novo
  smoke integra o runner utilizado pelas futuras execuções de CI.
- [Matriz própria](composition-evidence-0.3.json): 486 roundtrips em nove
  projeções, três bearings e dois DPI; 108 casos de interseções amostradas
  dentro do frame. Erros máximos registrados por espaço. Não é oracle externo
  nem promessa de exatidão analítica para qualquer projeção/borda.
- Exemplos [mapa limpo](../examples/clean_map.py) e
  [atlas](../examples/composition_atlas.py): PNG/SVG/HTML exportados, PNGs
  inspecionados e SVG/XML validado; [hashes e proveniência](_static/composition/README.md).
  Natural Earth permanece domínio público; rotas e símbolos são sintéticos.
- Instalação nova offline sem extras preserva SVG/HTML, dados/fontes e os
  novos contratos de transform/composição. Wheel/sdist reconstruídos, conteúdo
  e metadata BSD-3-Clause auditados, twine strict e notices conferidos.
- Integração corrigida para eixos isolados sem Figure, contextos de overview,
  transforms entre eixos/insets e cursor antes da pintura em vistas rotacionadas.
  A antiga entrada inválida NaN do teste de séries passou a infinity: NaN agora
  é gap suportado; a validação atômica de dados realmente inválidos permanece.

Limites explícitos: inversas mistas exigem separabilidade; Beziers usam
flattening determinístico, não adaptativo. Layout múltiplo exige regiões
disjuntas; compressed compacta grids completos sem spans/aninhamento. Textos
livres/cax reservam faixas de borda, sem solver universal de colisões interiores.
Datas/logs são números escalares, não eixos de latitude logarítmica. Handlers
customizados desenham PathPatch próprios. Bearing é rotação 2D isotrópica;
norte/rosa seguem a direção local da projeção e mantêm componentes independentes.
HTML rotacionado/curvo continua snapshot sem recomposição Python, conforme
[limites do viewer](visual-style.md); ponte viva permanece em 7.03.

O lote seguinte a este registro foi **5.01–5.08**: raster/terreno e mapas científicos 2D.
3D, animação, Qt e demais IDs permanecem pendentes; versão estável/main 0.2.0
preservada. Nenhum push, release ou upload PyPI é parte deste lote.


### Lote 5 — raster, terreno e mapas científicos 2D (0.3.0.dev0)

**5.01–5.08 concluídos no corte documentado.** [Contratos, unidades e limites](scientific-2d.md).
Implementações próprias em `scientific.py`, `scientific_artists.py`, `tri.py`,
`raster.py`, campos/axes/cores e integração renderer/colorbar/legenda existente.

- **5.01:** GeoRaster escalar/RGB/RGBA, máscara imutável, alpha e NoData;
  ColorImage editável, codecs genéricos limitados e mesma cena projetada PNG/SVG.
- **5.02:** inverse-affine/CRS e centros de pixels; nearest/bilinear,
  cobertura semiaberta, strict/renormalize e alpha premultiplicado.
- **5.03:** contourf com recorte linear por triângulos, união de fronteiras,
  furos/ilhas, FilledContourSet, níveis/cores editáveis e barras preenchidas.
- **5.04:** Delaunay regional próprio, interpolação baricêntrica, tripcolor/
  tricontourf, máscaras e erros de degeneração explícitos.
- **5.05:** heatmap, hist2d e density ponderado com resolução, extent,
  gaussiana que conserva massa e count/probability/density angular.
- **5.06:** FlowCollection de rotas geodésicas esféricas/elipsoidais,
  magnitude/cores/larguras e legenda temática; proxies de magnitude quiver.
- **5.07:** terrain RGB iluminado com ScalarMappable de elevação separado,
  hillshade próprio e composição com contornos/hidrografia sintética.
- **5.08:** RGBA com tipos de índices/máscaras, classes/norm/cmap/NoData
  vinculados a legendas/colorbars, incluindo edição de níveis preenchidos.
- Correção adicional: HandlerSymbol usa fator uniforme e centralização
  por bounds reais; triângulo do atlas deixou de se achatar na legenda.

[36 testes novos](../tests/test_scientific_foundation.py) verificam planos
analíticos, triângulos/circumcírculos, áreas/furos, conservação de pesos, alpha
e pixels exportados, edição sem mutação inválida, máscaras, classes e lifecycle.
[Wheel instalado](scientific-validation-0.3.json): **827 testes / 18.757
subtests**, zero falhas/erros; os mesmos cinco skips opcionais/permissionais
nomeados do lote anterior. Runtime e runner conferidos por hash contra a fonte.
Windows/CPython 3.14.4, Pillow/NumPy, sem aggdraw/Numba nem importação de
Matplotlib/GIS. Resultado local, não uma CI nova de três plataformas.

[Desktop instalado](scientific-desktop-0.3.json): dois smokes reais Tk em
janelas ocultas, incluindo novas edições científicas e composição rotacionada;
input sintético, sem novo aceite visual/input humano. O runner da futura CI
inclui o novo smoke. Instalação offline nova sem extras também executa SVG,
RGB/contourf/interpolação/resampling e preserva os contratos anteriores.
[503 casos próprios](scientific-evidence-0.3.json) de interpolação/conservação
e exportação estrutural; erro máximo observado 1,78e-15 nas fixtures, não um
oracle externo nem tolerância universal. [Galeria sintética](../examples/scientific_atlas.py)
em PNG/SVG/HTML, PNGs instalados inspecionados e [manifests/proveniência](_static/scientific/README.md).
Atlas de composição regenerado com a legenda corrigida.

Wheel/sdist de desenvolvimento reconstruídos; notices, recursos upstream,
licenças, exclusão do dado ODbL opcional, conteúdo/metadata, twine strict,
documentação e scanner de privacidade/refs locais fazem parte dos gates do lote.
Nenhuma nova base/font/ícone/paleta de terceiros foi incorporada.

Limites: representação por células vetoriais, não textura GPU; amostragem
in-memory; triangulação planar regional limitada e sem constrained/spherical
mesh. contourf é linear SW–NE, não idêntico ao interpolador bilinear de contour.
Density em graus², não população/km². Terreno iluminado é snapshot 2D, não
3D; recompute para mudar iluminação/elevação. Malha curvilínea direta, mosaico,
satélite volumoso, hidrologia, graph routing e flow bundling não fazem parte
deste corte. Níveis exteriores de contourf não são preenchidos implicitamente.

Próximo lote: **6.01–6.08**, acabamento visual, texto e exportação. Os passos
6–10 permanecem pendentes (**40 subpassos**); main/estável 0.2.0 preservados.
Nenhum push, release ou upload PyPI é parte deste lote.

### Lote 6 — acabamento, texto e exportação (0.3.0.dev0)

**6.01–6.08 concluídos no corte delimitado.** [Contratos completos](finishing.md)
e [galeria original com proveniência/hashes](_static/finishing/README.md).
Implementações próprias em `path.py`, `polygon_labels.py`, `curved_text.py`,
`mathtext.py`, `font_outline.py`, `patterns.py`, `icons.py` e `renderers/pdf.py`.
PNG/SVG/Tk preservam a arquitetura; savefig PDF estático também integra Save
nativo. Componentes continuam opcionais e a versão publicada não é alterada.

- [32 testes novos](../tests/test_finishing.py): Bézier analítica/erro,
  transforms/limites, clipping/caps fracionários, fases subpixel e todos os
  tipos de texto, expressões/erros/rotação, glifos simples/compostos,
  tamanho/xref/transparência/avisos/atomicidade e números PDF, anchors/holes,
  viewport/prioridade, leaders/obstáculos, curva/repetição/visibilidade,
  SVG limitado/finito/seguro/hash, tile/holes/limites e metadata PNG/SVG/PDF.
- [Suíte instalada](finishing-validation-0.3.json): **859 testes,
  19.937 subtests, zero falhas/erros**, skips opcionais/plataforma nomeados.
  Todos os módulos do wheel conferidos por SHA-256 contra o source final;
  runtime sem imports cartográficos/de referência externos. Windows local,
  CPython 3.14.4/Pillow/NumPy, sem aggdraw/Numba; isto não é nova CI remota.
- [Oráculo de fontes](finishing-font-reference-0.3.json): **22.392 glifos**
  das quatro faces, comparação com fontTools 4.66.0, diferença de pontos zero.
  Contornos não hintados; não é teste de shaping/rasterização. Fontes originais
  e avisos permanecem intactos. fontTools não entra no runtime.
- [Auditoria instalada](finishing-evidence-0.3.json): **3.003 casos analíticos**
  em tolerâncias .02/.1/.4 e PNG/SVG/PDF em 100/150/200 DPI. Exportações do
  atlas completo e SVG/ícone próprio; hashes/scripts registrados.
- [PDF independente](finishing-pdf-validation-0.3.json): pypdf estrito,
  Poppler, pagesize, anexo DejaVu exato/proveniência, nove probes de alpha
  com diferença de canais zero. Imagens finais inspecionadas; não promessa
  de identidade pixel a pixel entre rasterizadores.
- [Três smokes Tk](finishing-desktop-0.3.json): novo acabamento e regressões
  científico/composição aprovados em janelas reais retiradas da tela;
  edição/rotação/visibilidade/cleanup sintéticos, não aceite humano nativo.
- Wheel core offline sem extras aprova expressões/PDF/SVG e ambos os imports.
  Wheel/sdist reconstruídos; auditorias de avisos/assets/links, RECORD,
  conteúdo exato, privacidade do source/histórico/arquivos e fsck executadas
  no fechamento. Nenhuma publicação, push ou mudança em main.

Limites explícitos: contornos PDF sem texto pesquisável, uma página, famílias
DejaVu incorporadas; raster 2D em cells pode gerar PDF grande. Expressões
simples não são TeX/MathText completo; hinting subpixel/shaping generalizado,
SVG completo e fonts variáveis não são prometidos. Curved names simples,
prioridade/colisão conservadoras, budget interior e snapshot HTML documentados.
Etapas 7–10 permanecem pendentes: **32 subpassos**; nenhum ID foi eliminado.

### Lote 7 — interação, integração e desempenho (0.3.0.dev0)

**7.01–7.07 concluídos no corte documentado; 7.08 permanece pendente por
plataforma.** Implementação própria em `picking.py`, `widgets.py`,
`interaction.py`, `simplify.py`, `backends/live.py`, `backends/qt.py` e
`backends/notebook.py`. [Guia e limites](interaction.md),
[galeria original inspecionada](_static/interaction/README.md),
[auditor de evidências](../tools/audit_interaction.py).

- Picking por feature/ponto com IDs/índices, tolerância física em pixels,
  holes/clipping, callbacks e picking individual; seletores/layers/sliders
  opcionais. [36 contratos](../tests/test_interaction_integration.py), incluindo
  mutação inválida sem efeito, desligamento/clear, navegação e visibilidade externa.
- Ponte Python `browser-live` explícita: snapshots SVG e recomposição Python nas
  nove projeções internas, callbacks na thread proprietária, fila e corpo limitados,
  token/Host/Origin local, timeout de conexão e encerramento com cliente incompleto.
  Cliente próprio verificado com [fixture Node/DOM](../tools/check_live_viewer.js).
  Não houve aceite em navegador real; a inspeção automatizada do navegador estava
  indisponível. Este backend inicial tem Home/Back/Forward/Pan/Zoom e downloads
  PNG/SVG; não declara o editor Subplots/PDF dos viewers nativos.
- Notebook: display_id/update e post_run_cell reais em IPython 9.17.1, atualização
  e cleanup; [evidência](interaction-notebook-0.3.json). SVG atualizável, não widget
  DOM com mouse; nenhuma equivalência a todos os frontends Jupyter foi declarada.
- Qt opcional: QWidget/toolbar próprios sobre o mesmo Pillow/scene, sem toolkit
  cartográfico externo, QTest nativo Windows/PySide6-Essentials 6.11.2 com picking,
  pan/histórico, widgets, largura física e fechamento. [Evidência](interaction-qt-0.3.json).
  Tk mantém os contratos anteriores e passa os dois smokes do runtime final,
  [relatório](interaction-desktop-0.3.json). As 17 integrações Tk amplas passaram
  [antes](interaction-desktop-regression-0.3.json) do último ajuste exclusivamente
  HTTP; o auditor verifica que somente `backends/live.py` difere nesse relatório.
  Os relatórios são preservados sem substituir hashes de execuções anteriores.
- Simplificação de linhas optativa por erro projetado em pixels, markers originais,
  exportação estática com geometria integral; cache de 4 MiB. Fronteiras regionais
  com edges exatamente coincidentes compartilhadas uma vez, IDs/anéis preservados
  e rejeição explícita de topologia/vertexização não suportada. Sem snapping/overlay.
- [Benchmark reproduzível](interaction-benchmark-0.3.json): 400 ruas/20 labels e
  5000 pontos sintéticos, 640×480, quatro amostras. Pan completo mediano cerca de
  261/309 ms; primeira pintura cerca de seis segundos. Mede Python/caches, não
  memória nativa/RSS/FPS/latência humana. SVG/PDF/PNG registrados por bytes/hash.
  Círculos sólidos usam área analítica, alpha/clipping e annulus próprios; preview
  quantiza centro até 1/32 pixel para cache, mantendo tamanho/espessura. Settled e
  exports são exatos. Baselines legados congelados conservam comparação exata para
  sua geometria poligonal; novos círculos têm testes matemáticos e de bands/PNG.
- [Suíte instalada com aggdraw](interaction-validation-0.3.json):
  **896 testes / 19,957 subtests**, zero falhas/erros.
  [Suíte instalada sem aggdraw/Numba](interaction-core-validation-0.3.json):
  **896 testes / 19,941 subtests**, zero falhas/erros.
  Skips opcionais nomeados; todos os módulos instalados conferidos por hash contra
  o source, nenhum import de referência/GIS. Core também instalado offline sem
  extras, com picking/simplificação/SVG e imports públicos verificados.
- Extras Qt/IPython resolvidos separadamente, com avisos e
  [inventário observado](interaction-dependencies-0.3.json); nenhum binário/código
  dessas dependências foi vendorizado. BSD e termos próprios de Natural Earth,
  DejaVu/ColorBrewer/CC0 permanecem. O gate de distribuição confere bytes, RECORD,
  metadata/licenças; documentação/API, privacidade e Git conferidos localmente.

**Falta em 7.08:** executar Tk/Qt em Linux e macOS e registrar seus resultados
nativos. A CI foi estendida com Qt/IPython e fixture Node (27 jobs expandidos),
mas não foi executada remotamente neste lote. Windows programático/pintura está
validado; não equivale a novo aceite humano de fluidez em três sistemas. Nenhuma
publicação, push ou mudança do `main`/versão estável 0.2.0 faz parte deste lote.

### Lote 8 — terreno 3D experimental (0.3.0.dev0)

**8.01–8.08 concluídos no contrato experimental; 7.08 continua pendente.**
[Guia e limites](terrain3d.md), [galeria original](_static/terrain3d/README.md),
[37 contratos](../tests/test_terrain3d.py) e [auditor das evidências](../tools/audit_terrain3d.py).

- Unidades físicas m/km/ft/Unit, Z físico separado do exagero; GeoRaster com
  affine completa usa centros de pixels e referencial horizontal local WGS84
  explícito, até 250 km da origem. Não inventa/converte datum vertical.
- Câmera ortográfica/perspectiva, matrizes, seis planos de clipping homogêneo,
  triângulos, cobertura top-left e depth buffer próprios. Triângulos cruzados
  verificam oclusão por pixel, sem ordenar faces pelo centro. Equações NumPy e
  fallback próprio conferidos; cancelamento e limites antes das grandes alocações.
- SurfaceArtist com scalar array/norm/cmap/clim/colorbar editáveis, visibilidade,
  remoção e iluminação plana. Máscaras retiram células; cores são escalares médios
  por face. Construções simples côncavas recebem piso/teto/paredes, IDs e base/altura
  explícitas. Sem transparência parcial, holes, picking 3D ou altura urbana inferida.
- Órbita e zoom separados dos limites geográficos 2D; Home/Back/Forward guardam
  Camera. [Tk Windows](terrain3d-tk-0.3.json) e [Qt Windows](terrain3d-qt-0.3.json)
  programáticos com pintura, mudança de pixels e cleanup; não equivalem a aceite
  humano ou nativo Linux/macOS. Cache inclui triângulos para não reusar pose antiga. Sharing físico/geográfico
  é rejeitado antes de alterar grupos, inclusive em chamadas diretas.
  [Regressões Tk selecionadas](terrain3d-desktop-0.3.json) e
  [Qt 2D](terrain3d-qt-2d-0.3.json) passam no mesmo runtime.
- PNG estático próprio; SVG embute PNG, PDF usa RGB comprimido com soft mask,
  preservando textos/eixos vetoriais. Pixel/alpha/orientação dos streams conferidos;
  exportação inspecionada por PNG e figura Qt. HTML offline é snapshot 3D, não órbita.
  Diferenças de antialiasing são declaradas; nenhuma exportação de modelo/GPU prometida.
- [Suíte instalada](terrain3d-validation-0.3.json): **933 testes / 19,963 subtests**,
  zero falhas/erros. [Sem aggdraw/Numba](terrain3d-core-validation-0.3.json):
  **933 testes / 19,947 subtests**, zero falhas/erros. Skips opcionais nomeados,
  todos os módulos conferidos por SHA-256; zero imports de Matplotlib/GIS externo.
- [Benchmark](terrain3d-benchmark-0.3.json): raster 320×240, três amostras após
  warmup; 450 triângulos sem NumPy ~46 ms, 1,922 com NumPy ~93 ms e 7,938 ~453 ms
  medianos. Exclui composição/GUI, RSS, GPU e latência humana/FPS. Budget: 50 mil
  vértices por malha, 20 mil triângulos por axes, 8M pixels e 64M testes bbox por
  rasterização; PNG conta supersampling. Não existe LOD automático ou terreno global.
- Instalação core offline sem extras também verifica câmera/raster fallback/PDF 3D
  e falha explícita do encoder SVG opcional. Wheel/sdist dev reconstruídos e conferidos
  por bytes/RECORD/licenças; documentação, privacidade e refs locais auditados.
  Termos de DejaVu/ColorBrewer/CC0/Natural Earth preservados. Nenhum novo material
  de terceiros foi vendorizado. CI preparada para smoke 3D, não executada remotamente.

Relatórios das etapas anteriores são snapshots preservados de seus runtimes;
nunca recebem hashes falsamente atualizados. A referência corrente desta etapa
é verificada por `audit_terrain3d.py`. **Restam 17 subpassos:** 7.08 e etapas
9–10. Nenhuma publicação, push, mudança do main ou lançamento 0.3.0 neste lote.


### Lote 9 — mapas temporais e atlas (0.3.0.dev0)

**9.01–9.08 concluídos; 7.08 permanece pendente.** [Guia](temporal.md),
[53 testes de contrato](../tests/test_temporal.py), [galeria original](_static/temporal/README.md)
e [auditor corrente](../tools/audit_temporal.py).

- TemporalSeries/Frame com payloads imutáveis, unidades numéricas explícitas,
  datas UTC, seleção exata/mais próxima/anterior/próxima e fontes finitas.
  Sem interpolação de instantes nem inferência de duração pelas datas.
- ScalarBinding prepara a série inteira antes de alterar imagens/malhas/pontos/
  coropletas ou cores de SurfaceArtist. Preserva geometria, posição, câmera e
  componentes estáticos; políticas global/por-frame explícitas e NoData.
  Norms/classes e colorbars/legendas seguem o vínculo existente; callbacks gerais
  reproduzíveis permitem alterar posições, áreas proporcionais, texto e rotas.
- FuncAnimation própria, pausa/retomada/seek/intervalo e controles optativos;
  timers Tk/Qt executam no thread GUI. Fechar a figura remove callbacks agendados,
  widgets e subscrições. Manual/headless/notebook/HTML não recebem threads ocultos.
- PNG por frames em diretório novo e GIF Pillow, exports atômicos e reaplicação
  do frame selecionado. GIF quantiza 10 ms e pode juntar imagens idênticas mantendo
  duração. Não se promete rollback de efeitos arbitrários de callbacks.
- Protocolo setup/write_frame/finish/abort e FFMpegWriter explícito, sem shell,
  download ou binário vendorizado; testes de argumentos/pipe/indisponibilidade/
  falhas. **Nenhum codec de vídeo instalado foi validado neste lote**. Dependências
  e obrigações do encoder escolhido permanecem separadas; MP4 requer dimensões pares.
- Atlas regional com estilo/projeção/tamanho comuns, limites reaplicados e páginas
  editáveis; sequências PNG/SVG/PDF e PdfPages próprio. Rebase de dicionários próprios,
  streams binários intactos, tamanhos físicos e avisos DejaVu preservados por página.
  [Leitor independente pypdf 6.10.0](temporal-pdf-0.3.json) confirmou três páginas e
  avisos exatos; Poppler externo renderizou a primeira para inspeção. Nenhum leitor/
  merger é backend ou material vendorizado da Azimlib.
- [Windows Tk](temporal-tk-0.3.json) / [Qt](temporal-qt-0.3.json): ticks automáticos,
  fim finito, pausa/retomada, slider/Play/intervalo e cleanup, sobre runtime instalado.
  [Regressões Tk 2D/3D](temporal-desktop-0.3.json) e
  [Qt 2D](temporal-qt-2d-0.3.json)/[3D](temporal-qt-3d-0.3.json) aprovadas.
  São provas programáticas nativas Windows, não aceite humano/FPS/Linux/macOS.
- [Suíte instalada com aggdraw](temporal-validation-0.3.json): **986 testes /
  19,987 subtests**, zero falhas/erros. [Sem aggdraw/Numba](temporal-core-validation-0.3.json):
  **986 testes / 19,971 subtests**, zero falhas/erros. Skips opcionais nomeados;
  111 módulos do runtime conferidos por SHA-256, zero imports Matplotlib/GIS externo.
- Galeria determinística de clima/população, comparações de normas, pontos
  proporcionais, GIF/frames e três regiões em PDF/SVG. SVG mantém aviso de fonte
  exato após XML decoding; exemplos exportados inspecionados. Dados temporais
  sintéticos; basemaps Natural Earth e fontes/paletas com seus avisos próprios.
- Carlito Bold Italic creditada voluntariamente na wordmark/manifest e avisos,
  conforme OFL 1.1/FAQ. Logo PNG intacta, nenhum binário de fonte Carlito distribuído;
  versão/hash da fonte de design não inventados. BSD da composição e código mantida.
- Wheel/sdist dev reconstruídos; instalação core offline, bytes/RECORD/metadata,
  avisos, documentação, privacidade/refs locais verificados. CI preparada para
  timers Qt nos três sistemas, **não executada remotamente**. Relatórios anteriores
  conservam seus hashes históricos; `audit_temporal.py` verifica o runtime corrente.

**Restam 9 subpassos:** 7.08 e 10.01–10.08. Sem push, mudança do main, PyPI ou
lançamento 0.3.0 neste lote. Budgets/limites da API inicial estão no guia; não é
animação infinita, compilador de vídeo incorporado nem compatibilidade integral
com todos os escritores/encoders/callbacks de outro framework.


### Lote 10 — documentação e gates de entrega (0.3.0.dev0)

**10.01–10.07 concluídos para os artefatos de desenvolvimento.**
10.08 (aceite/publicação final) permanece pendente, assim como 7.08.

- [Site versionado](documentation-site.md) com parser Markdown genérico opcional,
  layout próprio, busca por títulos, links/âncoras/ativos conferidos; preview
  local/artifact não é chamado de documentação hospedada.
- [Migração](migration-0.3.md): três exemplos executáveis SVG/PDF, ambos imports,
  edição, componente opcional, animação finita/atlas. [Estabilidade](api-stability.md)
  separa contratos públicos, experimentais e internos; CHANGELOG consolidado.
- [Galeria atual](gallery-0.3.md): seis categorias, 18 exports PNG/SVG/PDF,
  hashes de scripts/runtime/arquivos, origem sintética/Natural Earth/fontes/paletas.
  Texto/font notice preservado. Links antigos a arquivos locais de `gallery/`
  foram convertidos em referências de reprodução; não viraram URLs públicas falsas.
- [Baselines próprios](../tools/baselines/release030/README.md): styles/cells/depth,
  geometria/layout arredondados, duas tolerâncias de pixels, trabalho limitado,
  tempos quentes e geodésica equatorial analítica; sem promessa de FPS/RSS/GPU.
- Gate CI agora exige 28 identidades/SHAs/resultados exatos (15 suites, 6 accelerator,
  3 Tk, 3 Qt e documentação); 14 regressões rejeitam falsos positivos de URLs, matriz antiga, duplicatas,
  SHA antigo, jobs cancelados/skipped e publicação estável sem checklist/version.
  Configuração não é resultado hospedado. O upload PyPI continua manual separado,
  e candidatos de desenvolvimento/aceite incompleto são bloqueados.
- Licenças/privacidade/packaging e instalação core isolada conferidos no build dev;
  docs extra usa markdown-it-py/mdurl MIT externos, não vendorizados. Recursos
  anteriores mantêm seus termos/hashes; crédito Carlito permanece voluntário.
- [Novas propostas](future-versions.md): Sol/Lua ligados à Terra, corpos planetários
  e órbitas cumulativas, com modelos/precisão/unidades/proveniência e critérios
  científicos explícitos. Nenhuma implementação celeste ou prazo prometido.

Os relatórios antigos são snapshots preservados. A versão permanece **0.3.0.dev0**;
este lote não autoriza uma publicação automática 0.3.0 nem trata CI como aceite
humano Linux/macOS. Contagem final e evidência hospedada serão registradas ao
passar seus gates, sem reescrever resultados anteriores.

Documentação de desenvolvimento [hospedada por HTTPS](https://kernerian.github.io/azimlib/dev/):
[prova de hospedagem](documentation-hosting-0.3.json), 389 arquivos revisados,
9 PDFs decodificados e 33 metadados de imagens examinados; nenhum caminho
pessoal, marcador de conversa ou credencial encontrado no escopo verificado.
Amostras HTTPS conferidas byte a byte contra o site auditado. Dois relatórios
antigos preservam versões/testes e usam caminhos portáveis de ambiente.
O repositório principal e a versão PyPI permanecem inalterados.

A comparação raster conserva os hashes exatos de geometria/texto/estilo. Somente
caixas de texto têm comparação bidirecional com vizinhança de dois pixels, para
variações RAQM/FreeType. Diferenças brutas são registradas; desaparecimento de
texto, mudança de cor e tolerância fora de textos têm regressões negativas.

CI hospedada [28/28 aprovada](https://github.com/Kernerian/azimlib/actions/runs/37662358024):
[auditoria dos 28 artefatos](delivery-ci-0.3.json), 1.000 testes em cada um dos
15 jobs de Python/sistema, 19 integrações Tk por sistema, Qt 2D/3D/temporal e
notebook em três sistemas, seis jobs com acelerador e documentação executável.
Hashes instalados conferidos contra os blobs exatos do commit testado; as
diferenças locais registradas são somente transporte LF/CRLF. Logs ZIP/CRC e
report hashes foram conferidos, incluindo licenças/privacidade/distribuição.

**Restam 2 subpassos: 7.08 e 10.08.** CI programática nativa não substitui
conferência visual/input humana Linux/macOS. Não houve publicação 0.3.0 no PyPI.


### Rodada visual 7.08 — aguardando aprovação humana

[Procedimento e checklist](visual-review-0.3.md): artifacts separados Ubuntu/macOS,
14 cenas PNG/SVG, referências próprias Windows, 100/200 dpi e capturas nativas
Tk/Qt (urban/pan/Home/Subplots/3D/temporal). O workflow gera material de revisão;
seu sucesso não equivale a aceite humano. **7.08 e 10.08 continuam pendentes.**
Nenhuma publicação de site, release ou pacote é executada por esse workflow.
