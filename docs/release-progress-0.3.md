# Progresso da Azimlib 0.3.0

Status: **em desenvolvimento, não publicada**. A versão estável publicada é 0.2.0.
Esta é a checklist operacional única; os IDs são estáveis. O [registro da 0.2.0](release-progress.md) permanece separado.

**16 concluídos / 64 pendentes**. Contagem por subpassos, não por frentes amplas.

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

- [ ] **3.01** Modelo de elipsoide, parâmetros de datum e unidades com contratos públicos.
- [ ] **3.02** Geodesia elipsoidal direta/inversa com convergência e casos quase antipodais verificados.
- [ ] **3.03** Transversa de Mercator/UTM próprias, zonas/hemisférios e transformações inversas.
- [ ] **3.04** Projeções adicionais prioritárias: estereográfica e azimutal equidistante.
- [ ] **3.05** Viewport atravessando antimeridiano, incluindo navegação, ajuste de limites e exportação.
- [ ] **3.06** Recorte esférico de linhas/polígonos com horizonte e casos degenerados documentados.
- [ ] **3.07** Topologia básica: testes de interseção, orientação e validação de anéis/fronteiras.
- [ ] **3.08** Matriz numérica de forward/inverse, singularidades, tolerâncias e dados em CRS explícito.

## 4. Transforms, Artists, escalas e composição

- [ ] **4.01** Transforms composáveis geo/projetado/axes/figure/display com inversas e unidades físicas.
- [ ] **4.02** Transforms mistos e vínculo de objetos existentes sem quebrar coordenadas geográficas.
- [ ] **4.03** Linhas com gaps NaN/máscaras, Paths públicos e coleções editáveis em lotes.
- [ ] **4.04** Locators/formatters de datas e logs; contrato de escalas separado de CRS/latitude.
- [ ] **4.05** Ticks de graticules em bordas curvas e offsets científicos consistentes.
- [ ] **4.06** SubFigure e solver para múltiplos GridSpecs raiz, preservando posições explícitas.
- [ ] **4.07** Layout compressed, obstáculos de textos livres/cax e critérios de convergência.
- [ ] **4.08** Ciclos de estilo nas demais famílias, símbolos reutilizáveis e handlers de legenda personalizados.

## 5. Raster, terreno e mapas científicos 2D

- [ ] **5.01** Raster RGB/RGBA, máscaras/NoData e exportação consistente.
- [ ] **5.02** Resampling nearest/bilinear de campos geográficos com cobertura e NoData.
- [ ] **5.03** contourf próprio, níveis discretos, holes e ligação a ScalarMappable/colorbar.
- [ ] **5.04** Campos irregulares e triangulação inicial própria com degenerações explícitas.
- [ ] **5.05** Heatmaps/densidade, normalização, amostras ponderadas e controles de resolução.
- [ ] **5.06** Fluxos/vetores geográficos e rotas geodésicas com legendas temáticas.
- [ ] **5.07** Hipsometria/hillshade/topográfico: composição raster + contornos + hidrografia.
- [ ] **5.08** Colorbars/legendas: máscaras, atualização de classes, norm/RGBA e edição vinculada.

## 6. Acabamento visual, texto e exportação

- [ ] **6.01** Curvas/caps/junções e clipping fracionário: testes PNG/SVG no mesmo DPI.
- [ ] **6.02** Tipografia subpixel e métricas/hinting, com auditoria de todos os tipos de texto.
- [ ] **6.03** Âncoras interiores de polígonos, prioridade e colisões de labels/leader lines.
- [ ] **6.04** Textos ao longo de curvas e repetição de nomes em ruas/rios extensos.
- [ ] **6.05** Expressões matemáticas simples próprias e documentação das limitações de shaping.
- [ ] **6.06** Símbolos/ícones externos e padrões customizados com proveniência explícita.
- [ ] **6.07** Exportador PDF vetorial próprio, incluindo transparência e estratégia de fontes/avisos.
- [ ] **6.08** Galeria comparativa de mapas completos e componentes, sem copiar assets/implementação de referência.

## 7. Interação, integração e desempenho

- [ ] **7.01** Picking de features e seleção com tolerância em pixels e callbacks.
- [ ] **7.02** Seletores, controle de camadas e sliders próprios, sem componentes obrigatórios.
- [ ] **7.03** Ponte viva Python/viewer portátil para atualização/reprojeção em todas as projeções suportadas.
- [ ] **7.04** Integração notebook com lifecycle/event loop e atualização de Figures.
- [ ] **7.05** Backend Qt opcional próprio usando o mesmo canvas/renderer e comandos de navegação.
- [ ] **7.06** Simplificação por erro em pixels, compartilhamento de fronteiras e caches incrementais.
- [ ] **7.07** Benchmarks urbanos/densos: primeira pintura, pan, labels, memória e exportação.
- [ ] **7.08** Validação nativa Tk/Qt por plataforma e manutenção da fluidez/espessura física de linhas.

## 8. Terreno 3D experimental verdadeiro

- [ ] **8.01** Contrato de coordenadas de elevação/unidades; separar altura física de exagero vertical.
- [ ] **8.02** Câmera própria ortográfica/perspectiva e transforms mundo/view/clip/display.
- [ ] **8.03** Clipping 3D, raster de triângulos e depth buffer próprios, incluindo oclusão.
- [ ] **8.04** Artist de superfície/terreno com cores/norm, iluminação e máscaras.
- [ ] **8.05** Extrusão inicial de plantas de construções com altitude/base explícitas.
- [ ] **8.06** Órbita/zoom da câmera e reset, mantendo separada a navegação de mapas 2D.
- [ ] **8.07** PNG 3D e política explícita para exportação SVG/PDF com camada raster.
- [ ] **8.08** Galeria, testes de câmera/profundidade e limites de desempenho da API experimental.

## 9. Mapas temporais e atlas

- [ ] **9.01** Modelo de frames e dados temporais, unidades/datas e seleção de instante.
- [ ] **9.02** Artist/scene updates por frame, preservando mapa e componentes estáticos.
- [ ] **9.03** Playback, pausa, slider, intervalo e encerramento de timers sem recursos pendurados.
- [ ] **9.04** Escalas de cores/legendas globais ou por frame com comportamento explícito.
- [ ] **9.05** Exportação de sequência PNG e GIF via dependência genérica opcional.
- [ ] **9.06** Protocolo de encoder de vídeo opcional com dependências/erros documentados.
- [ ] **9.07** Atlas por páginas e séries regionais com vistas/estilos compartilhados.
- [ ] **9.08** Exemplos temporal/populacional/climático sintéticos e testes de repetibilidade.

## 10. Documentação, compatibilidade e entrega

- [ ] **10.01** Documentação versionada/hospedada e guias de migração Matplotlib → Azimlib.
- [ ] **10.02** Galeria política/física/urbana/científica/3D/temporal com scripts e proveniência.
- [ ] **10.03** Contrato de compatibilidade/semver, API experimental e changelog completo.
- [ ] **10.04** Auditoria de licenças/proveniência/privacidade de todas as novas fontes e assets.
- [ ] **10.05** CI completa nos sistemas/Pythons suportados, incluindo novos readers e backends opcionais.
- [ ] **10.06** Baselines visuais/numericamente verificáveis e gates de desempenho reproduzíveis.
- [ ] **10.07** Atualizar versão/metadata, reconstruir wheel/sdist e testar instalação isolada/imports.
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
