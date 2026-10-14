# Progresso da Azimlib 0.4.0

Status: **em implementação; etapas 1, 3, 4, 5, 6, 10, 11 e 12, 2.01–2.07, 7.01–7.08, 8.01–8.08, 9.01–9.07, 13.01–13.05, 13.08, 14.01 e 14.06 validados localmente**.
**102 concluídos / 10 pendentes**. São 14 etapas e 112 subpassos com IDs estáveis;
essa contagem descreve entregáveis, não horas nem uma estimativa de duração.
A versão publicada permanece 0.3.0, com [entrega concluída](release-publication-0.3.0.md)
e [checklist histórica 80/80](release-progress-0.3.md). Planejar não conclui os IDs abaixo.

## Escopo e rastreabilidade

Este corte reúne todas as reservas explícitas da checklist 0.3.0 e as propostas
de Sol/Lua e geometria celeste terrestre. Nenhuma reserva antiga foi removida.

| Origem técnica | Etapas da 0.4.0 |
| --- | --- |
| [Reserva 0.3: volumes 3D, nuvens volumétricas e GPU](release-progress-0.3.md) | 9 e 10 |
| Reserva 0.3: OSM PBF completo e streaming em escala planetária | 2 |
| Reserva 0.3: CRS universais e datum por grids oficiais | 3 |
| Reserva 0.3: overlay/union globais de topologia arbitrária | 4 |
| Reserva 0.3: geocodificação e roteamento urbano completos | 5 e 6 |
| Reserva 0.3: TeX completo e shaping internacional complexo | 7 e 8 |
| [Novas propostas: Sol, Lua, sombras e eclipses](future-versions.md) | 11, 12 e 13 |
| Fundação cumulativa, compatibilidade e gates de entrega | 1 e 14 |

Cartografia planetária pública (Beyond Earth) continua na 0.5.0; Sistema Solar
genérico e referenciais orbitais (Orbits) continuam na 0.6.0. A 0.4.0 prepara
corpo/frame/unidades/tempo compartilhados, mas mantém foco terrestre e Terra–Lua.
Essas extensões complementam, não substituem, manutenção urbana e cartográfica.

## Regras de conclusão

- Cada ID exige implementação funcional, contratos/erros, regressões e documentação;
  novas capacidades não são anunciadas a partir de APIs vazias ou screenshots.
- Cada lote mantém origem/licença de dados, fontes e algoritmos, testes numéricos,
  revisão de privacidade e exportações reproduzíveis conforme seu domínio.
- Runtime cartográfico e implementações geográficas continuam próprios. Bibliotecas
  genéricas de baixo nível e motores tipográficos opcionais podem ser usados com
  dependências e licenças explícitas; não delegar cartografia a um motor GIS externo.
- Preservar imports, comportamento familiar, estilos físicos e Artists editáveis.
  Componentes cartográficos permanecem opcionais; `savefig()` e `show()` são separados.
- Cobertura de PBF, CRS/grids, topologia, TeX e modelos celestes deve ser verificável
  e publicada. Termos amplos como universal/completo não autorizam alegações de
  suporte irrestrito a toda variante, datum, macro, geometria ou época existente.
- Modelos celestes exigem frames, unidades, escalas de tempo, validade e precisão
  registradas. Iluminação bonita não constitui prova de posição/evento correto.
- Datas, contagens e resultados de CI/benchmarks pertencem ao commit testado.
  Limitações não resolvidas mantêm os respectivos IDs pendentes.
- Mudanças de escopo exigem registro de motivo e destino de cada item; não apagar
  IDs nem reduzir silenciosamente o total. Publicação requer aceite explícito.

## Dependências e lotes

| Lote | Etapas | Dependências principais |
| --- | --- | --- |
| A — fundação | 1 | Contratos atuais da 0.3.0 |
| B — dados e geometria | 2, 3, 4 | 1; integração entre PBF, CRS e topologia |
| C — urbano operacional | 5, 6 | 1, 2, 3 e operações necessárias de 4 |
| D — texto científico/internacional | 7, 8 | 1; 8 reutiliza métricas e composição de 7 |
| E — renderização avançada | 9, 10 | 1; 9 integra texto de 7; 10 usa 9 e câmera 3D existente |
| F — céu terrestre | 11, 12 | 1 e CRS/frame de 3; fases de 12 usam a geometria solar de 11 |
| G — iluminação integrada | 13 | 9, 11, 12; ligação a volumes após 10 |
| H — consolidação | 14 | Todos os anteriores; auditorias e testes entram em cada lote |

A implementação pode intercalar frentes independentes após a fundação. Fechar
lotes grandes e coerentes, sem saltar dependências ou deixar integração para o fim.
Não há prazo prometido; o volume e a dificuldade são maiores que os da 0.3.0.

## 1. Fundação compartilhada, compatibilidade e contratos

- [x] **1.01** Inventariar APIs e limites da 0.3.0; estabelecer matriz de regressão para mapas, urbano, texto, 3D, tempo e ambos os imports.
- [x] **1.02** Definir unidades, precisão numérica, convenções de eixos e propagação de erros para todos os novos subsistemas.
- [x] **1.03** Criar abstrações internas compartilhadas de corpo, frame e transformações; manter Terra como padrão sem antecipar a API planetária pública da 0.5.0.
- [x] **1.04** Definir instantes, escalas de tempo, calendários e conversões UTC/TT/UT1 aplicáveis, com fontes de offsets e limites de validade explícitos.
- [x] **1.05** Definir observador geográfico: longitude, latitude, elevação, horizonte e distinção entre posição geocêntrica, topocêntrica e aparente.
- [x] **1.06** Especificar extensões do renderer para recursos GPU, volumes, iluminação e texto, com capacidades consultáveis e backend CPU preservado.
- [x] **1.07** Estabelecer budgets mensuráveis de memória, latência, precisão e tamanho dos datasets; separar medição sintética de ensaio em dados reais.
- [x] **1.08** Fixar fixtures próprias ou licenciadas, fontes primárias de validação e contratos de erro/visibilidade/edição/exportação antes de implementar os lotes dependentes.

## 2. OSM PBF e streaming de grande escala

- [x] **2.01** Implementar enquadramento binário PBF e decodificação dos tipos necessários do protocolo, sem delegar a interpretação geográfica a outro leitor.
- [x] **2.02** Implementar string tables, nodes/dense nodes, ways, relations, IDs, deltas, granularity e offsets, preservando a semântica dos atributos.
- [x] **2.03** Implementar descompressão por codecs genéricos suportados e limites contra blocos inválidos; diagnosticar variantes não suportadas.
- [x] **2.04** Resolver referências entre blocos com índices em disco ou estratégia equivalente, mantendo consumo limitado de memória.
- [x] **2.05** Interpretar multipolígonos, fronteiras e relações de restrição necessárias ao urbano/roteamento, incluindo referências incompletas.
- [x] **2.06** Adicionar filtros espaciais e por atributos e extração regional sem carregar implicitamente o planeta inteiro.
- [x] **2.07** Integrar catálogo opcional, aquisição explícita, versão/hash, licenças OSM/ODbL e política de metadados pessoais; não incorporar bases grandes no wheel.
- [ ] **2.08** Validar leitor completo no contrato declarado, equivalência com fixtures XML, dados corrompidos, memória e ensaio reproduzível de streaming em escala planetária.

**Pendência exclusiva de 2.08: ensaio real com o dump planetário completo.**
A implementação necessária existe; PBF real menor, streaming, referências em
disco, filtros, corrupção, equivalência XML e limites de recursos já foram
validados nas [evidências por lote](#evidências-por-lote). Falta exclusivamente executar e validar
o processamento integral de `planet.osm.pbf`. Nenhum resultado regional ou
sintético substitui esse critério. A pendência não bloqueia etapas independentes
seguintes da 0.4.0; **revisitar obrigatoriamente antes do gate final da release**.
O [procedimento planetário](planet-trial.md) fixa entrada, budgets, métricas e
provas de conclusão. Não baixar nem executar esse dump no ambiente atual.

## 3. CRS, datums, épocas e grids oficiais

- [x] **3.01** Definir a matriz de cobertura: identificação de CRS, representações textuais, unidades, ordem de eixos, áreas de uso e erros para operações indisponíveis.
- [x] **3.02** Implementar catálogo versionado com origem/licença, lookup explícito e composição de pipelines, sem delegar transformações a um motor GIS externo.
- [x] **3.03** Ampliar famílias de projeções e inversas e integrar coordenadas geográficas, projetadas e geocêntricas nos readers e Artists existentes.
- [x] **3.04** Implementar operações de datum parametrizadas com convenções, épocas, unidades e domínio de validade explícitos.
- [x] **3.05** Implementar leitura/interpolação dos formatos de grids selecionados e suportados; preservar NoData, bordas e precisão publicada.
- [x] **3.06** Implementar seleção e inversão de operações horizontais/verticais e encadeamentos dependentes de época quando houver modelos válidos.
- [x] **3.07** Gerenciar grids oficiais como dados opcionais auditados, com versão/hash/licença e aquisição explícita; ausência de grid não pode provocar transformação aproximada silenciosa.
- [x] **3.08** Validar operações contra fixtures primárias independentes, ida/volta, limites de área/época, descontinuidades e integração com raster, viewport e exportação.

## 4. Topologia e overlay global

- [x] **4.01** Definir semântica planar/esférica, orientação/interior, holes, multipolígonos, tolerâncias e operações sobre entradas inválidas.
- [x] **4.02** Implementar predicados robustos, índice espacial e noding, incluindo cruzamentos, contatos, segmentos coincidentes e degenerações.
- [x] **4.03** Construir representação topológica compartilhada e rastreabilidade das features e arestas durante operações.
- [x] **4.04** Implementar interseção, união, diferença e diferença simétrica para linhas/polígonos, preservando holes, multipartes e atributos conforme política explícita.
- [x] **4.05** Tratar antimeridiano, polos, regiões maiores que um hemisfério e interiores globais sem reduzir silenciosamente a operação a um plano regional.
- [x] **4.06** Oferecer validação e reparo opt-in, com diagnóstico e relatório de mudanças; não modificar geometrias de entrada implicitamente.
- [x] **4.07** Integrar recorte, seleção, máscaras raster e fronteiras compartilhadas aos readers, camadas urbanas e renderers.
- [x] **4.08** Validar identidades de conjuntos, área/topologia, coincidências e casos adversariais globais, com benchmarks e cobertura suportada publicada.

## 5. Geocodificação, endereços e pesquisa urbana

- [x] **5.01** Definir modelos de endereço, localidade, POI e resultado, preservando IDs, fonte, precisão e distinção entre ponto e limite administrativo.
- [x] **5.02** Construir importação e índices locais a partir de bases opcionais licenciadas, incluindo bairros, ruas, números e aliases.
- [x] **5.03** Implementar normalização Unicode e pesquisa multilíngue, variantes de nomes e tokenização coerente com o sistema de texto.
- [x] **5.04** Implementar busca de endereços/POIs, ranking e filtros administrativos/espaciais, com resultados ambíguos explícitos.
- [x] **5.05** Implementar geocodificação reversa para localidades, vias e endereços com distância e nível de precisão informados.
- [x] **5.06** Tratar interpolação de endereços, cobertura incompleta e correspondências aproximadas sem inventar coordenadas ou certeza.
- [x] **5.07** Integrar resultados ao mapa/picking/labels; permitir provedores externos somente como opção explícita separada do índice e motor próprios.
- [x] **5.08** Validar consultas reais e sintéticas, ambiguidade, idioma, memória/latência, proveniência e privacidade dos dados de endereço.

## 6. Grafos e roteamento urbano

- [x] **6.01** Definir grafo próprio de nós/arestas, conectividade, geometria, unidades, custos e persistência de índices.
- [x] **6.02** Construir grafos a partir de vias OSM, separando cruzamento geométrico de conexão e respeitando pontes, túneis e níveis.
- [x] **6.03** Interpretar sentidos únicos, acesso, modalidades e restrições de conversão, incluindo relações aplicáveis entre vias.
- [x] **6.04** Implementar associação de origem/destino à rede e cálculos de caminho com custos e heurísticas próprios.
- [x] **6.05** Suportar perfis configuráveis de deslocamento, distância/tempo, pontos intermediários e rotas inviáveis com erros claros.
- [x] **6.06** Produzir geometria, trechos e instruções/atributos de rota com rastreabilidade; não confundir duração estimada com trânsito ao vivo.
- [x] **6.07** Integrar rotas, seletores, mapa urbano, escalas e playback; medir redes grandes sem bloquear o viewer.
- [x] **6.08** Validar caminhos ótimos conhecidos, restrições, direção, componentes desconexos, custos/unidades e desempenho em base real licenciada.

## 7. Texto internacional e shaping complexo

- [x] **7.01** Definir runs de texto, graphemes, scripts, linguagem, direção, fallback de fontes e métricas físicas comuns aos renderers.
- [x] **7.02** Implementar integração tipográfica de baixo nível, original ou licenciada/auditada, para bidi, contextualização, ligaturas e marcas combinantes.
- [x] **7.03** Adicionar seleção/fallback de fontes e cobertura auditada, com origens, licenças e políticas para fontes fornecidas pelo usuário.
- [x] **7.04** Aplicar posicionamento de glifos e métricas ao PNG, SVG, PDF e viewers sem duplicar a composição por backend.
- [x] **7.05** Integrar textos multilíngues a títulos, ticks, legendas, colorbars, annotations e labels geográficos editáveis.
- [x] **7.06** Adaptar texto em curvas, colisões, prioridades e leader lines para runs compostos, preservando legibilidade e âncoras.
- [x] **7.07** Definir acessibilidade, pesquisa/cópia e incorporação de fontes onde suportadas, com política explícita de outlines e fallback.
- [x] **7.08** Validar RTL/LTR misto, árabe, scripts índicos, CJK, acentos e diferentes DPI/rotações em três sistemas, incluindo licenças e inspeção visual.

## 8. TeX completo e composição científica

- [x] **8.01** Definir suporte real a TeX como opção tipográfica separada das expressões internas limitadas; registrar motor, dependências, licenças e contrato de cobertura.
- [x] **8.02** Implementar seleção/configuração explícita de motor e ferramentas auxiliares sem downloads ou instalações implícitos.
- [x] **8.03** Implementar compilação de documentos/fragmentos com diretório temporário controlado, limites de recursos e política explícita de acesso a arquivos/execução externa.
- [x] **8.04** Extrair métricas, baseline, caixas e saída do motor, integrando tamanho físico, alinhamento, rotação e transparência aos Artists.
- [x] **8.05** Suportar matemática, macros e preâmbulos no contrato declarado, sem apresentar o parser interno simples como TeX completo.
- [x] **8.06** Integrar SVG/PNG/PDF, cache por conteúdo/configuração/fontes e invalidação consistente nos viewers e exportações.
- [x] **8.07** Diagnosticar motor ausente, erros de compilação e fontes não disponíveis; fallback somente se explicitamente solicitado.
- [x] **8.08** Validar fórmulas, texto misto, baseline, edição e exportações nos sistemas suportados, inclusive avisos de ferramentas/fontes e instalação sem o extra.

## 9. Pipeline GPU e interação acelerada

- [x] **9.01** Selecionar API gráfica de baixo nível após avaliar portabilidade/licenças; manter geometrias, projeções e shaders cartográficos próprios.
- [x] **9.02** Implementar lifecycle de device/context/resources, capacidades e recuperação de falhas, com caminho CPU disponível.
- [x] **9.03** Implementar transformações, clipping, triangulação/upload e buffers de camadas, preservando a origem dos dados e precisão necessária.
- [x] **9.04** Renderizar linhas, marcadores, polígonos e raster com estilos, unidades físicas, transparência, z-order e antialiasing compatíveis.
- [x] **9.05** Integrar câmera/depth, terreno e extrusões 3D, texturas e iluminação, mantendo o mesmo modelo de cena/Artists.
- [x] **9.06** Integrar texto composto, picking e atualizações incrementais em pan/zoom/tempo; não mover composição geográfica para um engine externo.
- [x] **9.07** Garantir exportação estática, leitura de pixels e fallback explícito quando a GPU/driver estiver indisponível.
- [ ] **9.08** Medir primeira pintura, pan inicial/retomada, FPS/latência, memória e paridade CPU/GPU em hardware identificado; registrar diferenças visuais e CI sem GPU.
  Medições locais e capturas GPU em Windows/RTX 2060 disponíveis; workflow sem
  GPU nos três sistemas e referência Mesa/EGL preparados, ainda não executados.
  Composição de cena e preparação de meshes no zoom continuam gargalos; tempos
  de desenho isolados não comprovam latência física nem fluidez do viewer.
  Preservar o critério integral e revisitar antes do gate final da release.

## 10. Volumes 3D e nuvens volumétricas

- [x] **10.01** Definir campos escalares/vetoriais 3D, voxels, unidades, frame espacial, máscara/NoData e entrada por arrays ou arquivos de escopo declarado.
- [x] **10.02** Implementar streaming por blocos/bricks, seleção espacial e budgets de memória para volumes grandes.
- [x] **10.03** Implementar amostragem e composição volumétrica próprias com transfer functions, opacidade e referência de comprimento.
- [x] **10.04** Adicionar cortes, slices e isosuperfícies no contrato declarado, sem confundir nuvem de pontos com volume contínuo.
- [x] **10.05** Integrar GPU e caminho CPU de referência, profundidade/oclusão, terreno e georreferência em uma única cena.
- [x] **10.06** Implementar iluminação e sombras volumétricas compatíveis com o modelo declarado; distinguir visualização ilustrativa de simulação física.
- [x] **10.07** Integrar edição, picking, norm/colorbar, câmera e atualização temporal, com PNG/SVG/PDF e animação segundo política de rasterização explícita.
- [x] **10.08** Validar volumes analíticos, alpha/depth, NoData, nuvens sintéticas, precisão de amostragem, memória e desempenho; auditar qualquer dataset externo.

## 11. Sol e geometria solar terrestre

- [x] **11.01** Selecionar e documentar modelo solar, fontes, licença, escalas temporais, intervalo de validade e orçamento de erro antes de anunciá-lo.
- [x] **11.02** Criar objeto/Artist solar próprio e entrada manual por azimute e elevação, com convenções de origem e unidades explícitas.
- [x] **11.03** Calcular posição geocêntrica/topocêntrica/aparente por instante e observador, separando correções e refração opcionais.
- [x] **11.04** Calcular e visualizar trajetórias aparentes diárias e sazonais, incluindo solstícios e equinócios.
- [x] **11.05** Calcular ponto subsolar e terminador dia/noite sobre globo/mapas, respeitando projeção e antimeridiano.
- [x] **11.06** Calcular nascer/pôr e passagem pelo meridiano, com política de horizonte/refração e casos de dia/noite polar.
- [x] **11.07** Integrar edição, labels, picking e tempo ao mesmo sistema de Artists; fornecer vetor solar físico à iluminação do passo 13.
- [x] **11.08** Validar posições/eventos contra referências independentes auditadas, datas extremas e polos; publicar tolerâncias e exemplos estáticos/temporais.

## 12. Lua e visualização Terra–Lua

- [x] **12.01** Selecionar e documentar modelo/efeméride lunar, origem/licença, frames, escalas temporais, intervalo de validade e orçamento de erro.
- [x] **12.02** Criar objeto/Artist lunar próprio e entrada manual coerente com o frame e as unidades da cena.
- [x] **12.03** Calcular posição e distância geocêntrica/topocêntrica por data/hora, incluindo paralaxe e correções declaradas.
- [x] **12.04** Calcular ponto sublunar e posição relativa à Terra; integrar rótulos, projeções, unidades e picking.
- [x] **12.05** Visualizar órbita/trajetória lunar e playback temporal com distinção entre trajetória calculada e aproximação ilustrativa.
- [x] **12.06** Compor visualização 3D Terra–Lua com câmera existente, escala física versus visual explícita e oclusão correta.
- [x] **12.07** Calcular fases e orientação iluminada a partir da geometria Sol–Terra–Lua, vinculando a iluminação e tempo.
- [x] **12.08** Validar posição, distância, paralaxe, fases e animação contra referências auditadas; declarar validade e limites sem prometer astrodinâmica completa.

## 13. Iluminação, sombras e eclipses geométricos

- [x] **13.01** Definir luz solar, extensão angular, frames locais/globais, unidades e conexão da geometria celeste à cena 3D.
- [x] **13.02** Implementar incidência solar e iluminação de terreno/construções, separando altura física de exagero visual.
- [x] **13.03** Implementar sombras sobre terreno e entre construções com oclusão e tolerâncias de precisão declaradas.
- [x] **13.04** Implementar atualização temporal e sombras diárias/sazonais com cache/invalidação consistente nos caminhos CPU/GPU suportados.
- [x] **13.05** Representar umbra, penumbra e oclusão de fonte extensa na geometria Sol–Terra–Lua, sem regras decorativas específicas que finjam um eclipse.
- [ ] **13.06** Visualizar eclipses solares e lunares no contrato de precisão validado, distinguindo localização/instante físicos de escala visual exagerada.
- [ ] **13.07** Validar eventos e limites espaciais/temporais contra fontes independentes; manter o item pendente se a precisão não sustentar o resultado anunciado.
- [x] **13.08** Integrar mapas 2D, terreno 3D, volumes quando aplicável, componentes opcionais e exportação/animação, com exemplos e inspeção visual.

## 14. Integração, validação e entrega 0.4.0

- [x] **14.01** Executar regressões integradas de urbano, CRS, topologia, geocodificação/rotas, tipografia, GPU/volumes e Sol/Lua, preservando a simplicidade da API.
- [ ] **14.02** Publicar documentação e galeria reproduzível de todos os lotes, matriz de formatos/CRS/modelos/capacidades e guias de migração da 0.3.0.
- [ ] **14.03** Consolidar benchmarks de datasets grandes, memória e navegação, baselines numéricas/visuais e budgets com hardware/metodologia registrados.
- [ ] **14.04** Executar CI nos sistemas/Pythons suportados, cobrindo core sem extras, dependências opcionais e ausência de GPU/motores tipográficos.
- [ ] **14.05** Obter validação visual humana nativa Linux/macOS/Windows e registrar o escopo de viewer, texto, 3D/volumes, navegação e exportações.
- [x] **14.06** Auditar licenças/proveniência/privacidade de código, dados, grids, efemérides, fontes, shaders, documentação e histórico; manter termos de terceiros separados.
- [ ] **14.07** Preparar metadata/changelog, wheel/sdist, instalação isolada e auditorias de conteúdo/RECORD/hashes; não reutilizar resultados de outro commit.
- [ ] **14.08** Registrar aceite final do commit exato; somente com autorização explícita criar tag/Release, publicar bytes auditados, verificar PyPI, smoke limpo e documentação pública.

## Evidências por lote

Cada lote registra arquivos/commits, comandos, relatórios, modelos, tolerâncias,
exports e limites. Os resultados abaixo são locais; snapshots da 0.3.0 permanecem
intactos e não são reutilizados como validação da 0.4.0.


### Lote 1 — fundação compartilhada e contratos

**1.01–1.08 concluídos no escopo de fundação.** [Contratos, matriz de regressão,
fontes e limites](foundation-0.4.md), [evidência local](foundation-validation-0.4.json).

- `geodesy.Unit` reutilizado com SECOND/DAY; frames/corpo, transformação rígida,
  conversões geodéticas/XYZ e observador ENU próprios em `_frames.py`. LocalFrame
  do terreno usa as mesmas equações e cache de origem/base, sem alocações tipadas
  repetidas por vértice. Limites anteriores do terreno preservados.
- `_timescales.py`: UTC consciente de timezone, coordenada juliana em duas partes,
  TT/TAI/UT1 com offsets explicitamente fornecidos, fonte/validade/incerteza;
  nenhum leap/EOP atual é presumido ou baixado. Refração e efemérides não incluídas.
- `_contracts.py`: limites compartilhados e guardas de recursos; consultas de
  capacidades em `renderers.capabilities`. GPU, volumes e shaping complexo são
  declarados indisponíveis; lifecycle/extensões definidos para os lotes seguintes.
- Fixtures analíticas próprias BSD, fontes primárias NGA/IERS e contratos de
  precisão, erros, edição/visibilidade e exportação fixados antes dos próximos lotes.
- Suíte completa: **1031 testes / 20208 subtests**,
  zero falhas/erros; três skips explicitados (permissão de symlink e dois Numba).
  Windows/CPython 3.14.4, fonte local; não constitui nova CI remota.
- Benchmark próprio: **7000 roundtrips**, p95 de
  **13.319 ms por 1000**, pico de **241000 bytes**
  para 1000 pontos retidos, erro angular máximo 2.84e-14°
  e de altura 2.79e-09 m. Workload sintético,
  não evidência de ingestão planetária. Comparação local do terreno no relatório.
- Avisos/licenças e recursos de terceiros conferidos, verificação de privacidade
  dos arquivos alterados, sintaxe Python 3.10 e core SVG/PDF sem site-packages.
  Sintaxe não substitui execução futura da matriz Python/OS.

Reprodução: executar a suíte `tests/test_foundation_040.py` e regressões existentes
com `src` no import path; `python -I tools/benchmark_foundation.py --output benchmark.json`;
`python -I tools/audit_licenses.py`; `python -I tools/audit_publication_privacy.py`.
O teste de contagem mantém os 112 IDs e exige evidência para etapas concluídas.
Datas/modelos/corpos e APIs internos ainda podem evoluir; não houve tag, Release,
upload PyPI nem mudança da versão estável. Ao término daquele lote, etapas 2–14 permaneciam pendentes.


### Lote 2 — OSM PBF, referências em disco e extração regional

**2.01–2.07 concluídos no contrato declarado. 2.08 permanece pendente apenas
pela comprovação de escala planetária.** [Contrato e reprodução](osm-pbf.md),
[evidência local com hashes do fonte](pbf-validation-0.4.json).

- `_pbf_wire.py`, `_pbf_decode.py` e `pbf.py`: enquadramento/protobuf próprios,
  nodes/dense nodes/ways/relations, deltas/offsets e IDs inteiros; raw/zlib com
  descompressão limitada, corrupção diagnosticada e codecs não suportados explícitos.
- `OSMIndex`: índice SQLite descartável com orçamento de disco/cache, guarda de
  espaço livre, referências futuras entre blocos, ordenação por índices em disco,
  limpeza em falhas e liberação de consultas pausadas no Windows.
- Multipolígonos/fronteiras com anéis/holes e membros administrativos; restrições
  preservadas com from/via/to, conditional/except, sem alegar roteamento pronto.
  Referências incompletas rejeitadas ou omitidas com contagem por opção explícita.
- Filtros de atributos/envelopes, dateline conservadora e coleções com budgets
  separados; catálogo `osm-pbf` verifica bytes consumidos e avisos por streaming.
  Aquisição HTTPS separada, explícita, versionada e fixada por SHA256/ODbL integral.
- Fixtures originais cobrem XML/PBF equivalentes, registros entre blocos,
  variantes de codificação, corrupção, hashes, disco cheio/space reserve,
  filtros, cursores, memória streaming e integração urbana PNG/SVG.
- Suíte completa final: **1057 testes / 20302 subtests**,
  zero falhas/erros, três skips conhecidos; Windows/CPython 3.14.4 local.
  Sintaxe Python 3.10 verificada separadamente; nenhuma nova CI remota presumida.
- Extrato real Geofabrik Monaco 260101: **41.315 nodes, 6.168 ways, 347 relations**,
  60 relações poligonais e 43 restrições completas; **36 relações incompletas**
  reportadas com `missing='skip'`, sem geometrias truncadas. Índice **5.361.664 bytes**,
  pico Python **3476624 bytes**; pico do processo Windows
  **46321664 bytes**, incluindo imports/caches.
  Medição regional única, sem extrapolação de desempenho planetário.
- Base urbana XML congelada de São Paulo: **3.876 nodes / 464 ways / 464 features**
  equivalentes integralmente em IDs, coordenadas e tags após codificação própria
  para PBF de teste. O produtor real independente foi validado separadamente.
- Ensaio limitado a **20 GB totais e 15 GB de reserva livre**, sem baixar/executar
  planeta. O mesmo benchmark offline aceita futuro arquivo planetário e budgets
  adequados; `--scope planet` nunca conclui a prova automaticamente.

Reprodução: `tests/test_pbf.py`, regressões existentes, `tools/benchmark_pbf.py`,
`tools/acquire_osm_pbf.py` e `examples/osm_pbf.py`; comandos completos no guia.
Dados reais, índices e mapas de validação ficam fora do repositório/pacote.
Licenças/privacidade e docs foram verificadas localmente. Sem tag, Release,
publicação, mudança da versão estável ou modificação dos termos de terceiros.

### Lote 3 — catálogo, coordenadas 3D e operações parametrizadas

Escopo entregue: **3.01–3.04**; [contrato e matriz](crs-0.4.md).
Naquele corte, **3.05–3.08 ainda estavam pendentes**. A continuação abaixo
registra sua implementação e validação real independente; este snapshot
histórico não é reclassificado como ensaio do runtime posterior.

- Catálogo próprio versionado: 124 identidades, lookup explícito, definições
  imutáveis, ordem real/autoridade, unidades por eixo, área nominal/domínio e
  perfil textual próprio estritamente validado. WKT/PROJJSON não são inferidos.
- EPSG:4978/4979, altura explícita, conversão XYZ/UTM/geográfica, GeoJSON antes
  da validação e Artists PNG/SVG. Raster afim rejeita CRS 3D sem inventar altura.
- Lambert azimutal equivalente esférica com inversa, antiponto singular explícito,
  teste de área, integração regional e inversa de cursor portátil conferida em Node.
- Pipelines com identidades intermediárias exatas; conversões entre representações
  exigem o mesmo datum/realização; sem aproximação, operação ou aquisição implícita.
- Helmert 7/14 parâmetros, convenções position-vector/coordinate-frame, metros/
  arcsegundos/ppm e taxas por ano, época/validade/área explícitas, inversão exata da
  matriz avaliada. Fixture numérica primária IOGP 2019, sinais e casos sintéticos
  dinâmicos separados. Sem modelo de placa/geóide ou operação oficial presumida.
- Protocolo futuro de 2.08 reforçado com cgroup/quota, contagem integral de bytes,
  verificação SQLite e auditoria de todas as referências, inclusive relações raw.
  Nenhum dump planetário adquirido/executado e nenhum critério reduzido.

- Suíte completa: **1083 testes / 20641 subtests**, zero falhas/erros e três
  skips conhecidos (symlink e dois Numba opcionais), Windows/CPython 3.14.4.
  Conferência adicional do viewer/catálogo/protocolo/checklist: 49 testes aprovados.
- Benchmark sintético: 5.180 roundtrips XYZ; erro máximo angular 1.43e-14°,
  altura 1.50e-08 m. Não é validação de transformação oficial entre datums.
- Nova auditoria de referências do extrato Monaco: 673.493 bytes integralmente
  consumidos e hash conferido; zero nodes de ways ausentes. Os 33.551 membros
  externos ausentes das relações raw foram explicitamente contados; esse extrato
  regional não satisfaz a prova planetária, que exige ausência de referências perdidas.
- Licenças/recursos de terceiros, privacidade dos arquivos alterados, sintaxe
  Python 3.10 e core SVG/PDF/CRS sem site-packages conferidos localmente.

Reprodução: `tests/test_crs_040.py`, `tests/test_planet_protocol.py`, regressões
existentes e `examples/crs_pipeline.py`. [Snapshot final de evidências](crs-validation-0.4.json),
com hashes do runtime testado. Não constitui CI remota, publicação ou aceite
visual multiplataforma. Os snapshots dos lotes anteriores mantêm seus hashes
históricos; não são reclassificados como medições do runtime atual.

### Lote 3 — continuação: grids oficiais e operações horizontais/verticais

**3.05–3.08 concluídos; etapa 3 fechada em 8/8**, no contrato de cobertura
[documentado](datum-grids.md). [Evidências e hashes do runtime](grid-validation-0.4.json).

- NTv2 binário de ambos endians, hierarquia de subgrids, shifts e precisão
  float32; GTX binário NOAA 2009+, leitura própria em blocos e dados compactos.
  Limites de bytes/nós/tiles, corrupção, NoData, bordas, sinais e descontinuidades
  conferidos. Interpolação bilinear sem extrapolação ou fallback para grid pai.
- Operações horizontais/verticais com frame e referência de altura exatos;
  inversa horizontal iterativa com residual e diagnóstico de ambiguidade/não
  convergência; vertical com sinal explícito. Seleção local exige modelo único
  ou nome explícito, sem transformação aproximada quando faltam dados.
- Épocas/validade exigidas quando declaradas; composição com Helmert dinâmico
  preserva a mesma época e identidades intermediárias. Não inferir movimento de
  placa, deformação temporal ou terremotos a partir de um grid estático.
- Dois modelos oficiais LINZ opcionais, pacote 20200110, versão/commit/SHA-256
  fixados. Aquisição explícita/atômica com budgets de disco, atribuição LINZ,
  aviso original e CC BY 4.0 integral; nenhum payload no wheel/sdist.
- Validação primária em formatos independentes: **19.881 nós horizontais e 100
  células** contra ASCII LINZ; **651 nós verticais e 100 células** contra Sideris
  oficial (3.783.901 valores consumidos integralmente). Máximo erro: 2,385e-7
  arcsegundos horizontal e 5,173e-5 m vertical; tolerâncias 1e-6 arcsec/0,00011 m
  derivadas da precisão publicada, não alegações de acurácia de campo.
- **100 roundtrips reais**, máximo angular 5,685e-14°. Pico de alocações Python
  **20.656.359 bytes**, incluindo leitura dos grids, abaixo de 128 MiB; não é
  pico nativo/RSS. Dados/outputs locais sob 20 GB e reserva de 15 GB preservada.
- Raster de alturas exige frame compatível com CRS horizontal, corrige centros
  dos pixels e mantém NoData/referência vertical. PNG/SVG, viewport, colorbar e
  exemplo sintético próprios verificados; não há warp horizontal automático.
- Suíte final: **1109 testes / 20669 subtests**, zero falhas/erros e três skips
  conhecidos, Windows/CPython 3.14.4. Sintaxe Python 3.10, independência do core,
  licenças e privacidade verificadas localmente; nenhuma CI remota presumida.

Reprodução: `tests/test_datum_grids.py`, `tools/acquire_datum_grid.py`,
`tools/validate_datum_grids.py` e `examples/datum_grid_pipeline.py`.
O serviço de conversão online retornou HTTP 403; não se alega comparação ao
serviço. A evidência independente usa dados numéricos primários publicados,
com hashes e interpolação esperada calculada separadamente em Decimal.
Cobertura finita e variantes não suportadas continuam explícitas no guia.
**2.08 permanece pendente exclusivamente pelo ensaio planetário integral**,
sem alterar seu critério. A versão publicada e sua metadata permanecem 0.3.0.

### Lote 4 — topologia e overlay planar/esférico

**4.01–4.08 concluídos; etapa 4 fechada em 8/8**, no
[contrato de cobertura e precisão](topology-0.4.md).
[Snapshot de evidências e hashes do runtime](topology-validation-0.4.json).

- Núcleo planar próprio: predicados/construções com Fraction, índice STR
  conservador, noding de cruzamentos/contatos/coincidências e grafo compartilhado
  imutável com rastreabilidade por operando, parte, ring, segmento e direção.
- Interseção, união, diferença e XOR; holes/multipartes, linhas/pontos e contatos
  de dimensão inferior no plano. Conversão float64 de saída conferida; entradas
  inválidas/limites/ambiguidade falham explicitamente, sem snap/reparo implícito.
- Núcleo esférico próprio sobre vetores 3D e arcos menores de círculo máximo,
  sem redução a plano regional. Referência/interior explícitos, antimeridiano,
  polos, complementos maiores que um hemisfério e esfera cheia/vazia validados.
  Saída esférica regularizada; álgebra esférica geral de linhas/pontos e overlay
  elipsoidal não são anunciados. Tolerância angular e limites estão documentados.
- Reparo planar opt-in com antes/depois e relatório: deduplicação/winding ou
  reconstrução even-odd explícita; não inferir uma reparação esférica/altimétrica.
- Coleções lidas/urbanas: seleção/clip preservam objetos ou IDs/propriedades;
  overlay de Features mantém namespaces dos dois operandos. Máscaras raster
  classificam centros em lon/lat e preservam NoData/alpha/affine/CRS/height frame.
- Artists opcionais de fill amostrado e fronteira geodésica, editáveis e com
  limites explícitos de resolução. PNG/SVG conferidos visualmente; não se alega
  tesselação vetorial exata do fill nem alteração da topologia pela amostragem.
- Oráculos analíticos próprios: retângulos, cruzamentos racionais, área de
  polígono regular, lunes/hemisférios/octante e identidades de conjuntos/áreas,
  incluindo De Morgan e fixtures globais aleatórias determinísticas.
- Benchmark local: 2.000 segmentos separados, 0 pares candidatos contra
  1.999.000 pares brutos; pico Python 4,504,065 bytes
  abaixo de 128 MiB. Não é RSS nem ensaio planetário. Alguma validação e
  classificação permanecem quadráticas; tempos e tamanhos estão no snapshot.
- Suíte completa: **1132 testes / 21547 subtests**,
  zero falhas/erros, três skips conhecidos; Windows/CPython 3.14.4.
  Licenças/recursos auditados, sem novo código/dataset de terceiros neste núcleo.

Reprodução: `tests/test_overlay_040.py`, `tools/benchmark_topology.py` e
`examples/topology_overlay.py`. O exemplo global usa grade sem rótulos:
equivalentes de longitude podem colidir na costura/polo ortográfico do renderer
existente; **essa pendência visual fica registrada para 14.05**, não é declarada
corrigida pela topologia nem confunde área esférica com projeção.

**2.08 continua pendente exclusivamente pelo ensaio planetário integral**,
sem alteração de critério. Nenhuma publicação/CI remota é presumida; a versão
estável e sua metadata permanecem 0.3.0. Os snapshots anteriores não são
reclassificados como resultados do runtime deste lote.

### Lote 5 — geocodificação e pesquisa urbana locais

**5.01–5.08 concluídos; etapa 5 fechada em 8/8**, no
[contrato de cobertura, recursos e precisão](geocoding-0.4.md).
[Snapshot de evidências e hashes do runtime](geocoding-validation-0.4.json).

- Modelos imutáveis de origem, endereço, localidade/POI/via e resultado;
  IDs preservados, limite administrativo distinto do ponto representativo,
  precisão declarada/estimada explícita e atribuições por fonte.
- Índice próprio de tokens e tiles adaptativos, persistência SQLite genérica,
  construção atômica sem sobrescrita, reabertura somente leitura e SHA-256
  conferido. Importação de catálogo opcional e streaming do índice PBF próprio.
- NFKC/casefold/acento e aliases multilíngues preservam display original;
  pesquisa exata/prefixo e edição Levenshtein opt-in. Não se alega segmentação
  linguística, transliteração ou shaping. Mudança da versão Unicode exige rebuild.
- Ranking determinístico, filtros explícitos de endereço/administração,
  proximidade/bbox; ambiguidade e contagem total continuam visíveis com limit=1.
  Overflow de candidatos/vocabulário/JSON falha, sem resultado parcial disfarçado.
- Reversa por pontos, vias e limites regionais, incluindo poles/antimeridiano;
  distâncias esféricas, containment planar regional e precisão documentados,
  sem inventar acurácia cadastral, associação postal ou acesso à rede.
- Interpolação numérica explícita por IDs dos extremos, contexto, coordenadas,
  passo/paridade e comprimento geodésico esférico; sem extrapolação, associação
  à rua por proximidade, interpretação de sufixos ou confiança probabilística.
- Resultados integram camadas, picking real, labels/halo e PNG/SVG. Adaptador
  externo separado exige escolha explícita; nenhuma consulta/fallback automático.
- Privacidade: addr:* opt-in, contatos/notas/editores não importados, sem
  histórico de consultas/caminhos da origem. Bases/índices OSM preservam ODbL,
  copyright, atribuição e texto da licença; não são incluídos no wheel/sdist.
- Ensaio sintético com 5,000 registros e 40 consultas:
  mediana 3.86 ms, p95
  6.10 ms; índice
  2,732,906 bytes. São medições locais, não SLA.
- Ensaio real licenciado: 71 registros (64 vias, 7 POIs),
  64 consultas por nome e reversa; endereços residenciais não importados.
  Pico Python 11,577,833 bytes, abaixo de 128 MiB;
  não é RSS. Teto de 20 GB e reserva mínima de 15 GB preservados.
- Corrigido pico de leitura do catálogo: blocos de até 64 KiB, short reads e
  limite agregado, evitando alocar o teto de 256 MiB para um arquivo pequeno.
- Suíte completa: **1154 testes / 21635 subtests**,
  zero falhas/erros, três skips conhecidos; Windows/CPython 3.14.4.
  Core sem dependências opcionais, sintaxe Python 3.10 e auditorias locais de
  licenças/privacidade/distribuição conferidos. Não se presume CI remota.

Reprodução: `tests/test_geocoding_040.py`, `tools/validate_geocoding.py` e
`examples/local_geocoding.py`. Capacidade regional e cobertura incompleta são
explícitas; este lote não certifica uma base postal global nem escala planetária.
**2.08 continua pendente exclusivamente pelo ensaio planetário integral**,
sem alteração de critério; a pendência de rótulos na costura/polo ortográfico
continua em 14.05. A versão publicada/metadata permanece 0.3.0, sem publicação.

### Lote 6 — grafos e roteamento urbanos próprios

**6.01–6.08 concluídos; etapa 6 fechada em 8/8**, no
[contrato de cobertura, recursos e regras](routing-0.4.md).
[Snapshot de evidências e hashes do runtime](routing-validation-0.4.json).

- Grafo dirigido imutável com IDs de nós/vias, segmentos, geometria WGS84,
  comprimentos em metros, velocidades em km/h e duração estimada em segundos.
  Persistência atômica em diretório novo, manifest/schema/SHA-256, reabertura
  com reconstrução/verificação e avisos completos da fonte; sem overwrite.
- Importação própria de primitivas OSM XML e índice PBF em disco, com catálogos
  opcionais verificados. Só IDs de nós compartilhados conectam vias; cruzamentos
  geométricos, coordenadas coincidentes de IDs distintos, pontes e túneis não
  criam atalhos. Layer/bridge/tunnel são preservados; nós compartilhados de rampas
  permanecem conexões explícitas, sem reparo silencioso do dado.
- Perfis configuráveis de carro/bicicleta/pedestre: classes/velocidades explícitas,
  hierarquia de acesso, barreiras conservadoras, mão única/reversa/roundabout e
  overrides modais. Maxspeed numérico km/h/mph e direcional. Regras condicionais,
  direcionais de acesso ou desconhecidas reconhecidas falham explicitamente.
- Restrições no/only por nó via ou cadeia ordenada de vias via, exceções/modos,
  no_entry/no_exit com múltiplos membros, retorno distinto de continuação.
  Histórico de conversões preservado através de pontos intermediários/splits;
  conversão obrigatória para via inacessível não é descartada.
- Snapping esférico em segmentos, postings espaciais, raio/teto de candidatos,
  distância off-network separada e ambiguidades em vias coincidentes explícitas.
  Splits virtuais respeitam sentido e custo parcial, sem conectar redes distintas.
- Dijkstra e A* próprios, custo distância/tempo, heurística admissível e stops
  ordenados no estado global. Erros de referência, rota inviável, corrupção,
  limites de estados/fila/regras/disco e cancelamento não retornam rotas parciais.
- Geometria/trechos/instruções geométricas com rastreabilidade e licença. Camada
  editável/visível, picking real, escalas opcionais e playback por FuncAnimation
  próprio; executor não toca Artists, e aplicação exige thread solicitante.
- Ensaio sintético: 6,400 nós,
  25,280 arestas dirigidas, 40 consultas;
  A*/Dijkstra concordam. Mediana 77.38 ms,
  p95 600.14 ms sob tracemalloc;
  índice 658,128 bytes. Medições locais,
  não SLA nem alegação de desempenho planetário.
- Worker: 35 heartbeats do thread
  solicitante durante a busca; maior intervalo
  20.76 ms. Evidência
  de executor, sem alegar aceite humano Tk/Qt multiplataforma neste lote.
- Ensaio OSM real licenciado nos três perfis, com A*/Dijkstra concordantes;
  hash do extrato preservado, ODbL/copyright/atribuição/licença mantidos. Índices
  opcionais não entram nos archives. Sem contatos, editores, addr:* ou queries
  registradas. Pico Python 42,012,863 bytes, não RSS;
  teto de 20 GB e reserva mínima de 15 GB preservados.
- Suíte completa: **1178 testes / 22699 subtests**,
  zero falhas/erros e três skips conhecidos, Windows/CPython 3.14.4.
  Oráculo Floyd em todas as combinações de redes pequenas, snapping brute force,
  restrições conhecidas, equivalência XML/PBF, persistência e Artists cobertos.
  Core sem dependências opcionais, sintaxe 3.10 e auditorias locais documentados;
  não se presume CI remota ou inspeção humana dos viewers.

Reprodução: `tests/test_routing_040.py`, `tools/validate_routing.py` e
`examples/local_routing.py`. Não se alega navegação legal regional completa,
tráfego ao vivo, roteamento de caminhões/faixas/horários ou escala planetária.
**2.08 continua pendente exclusivamente pelo ensaio planetário integral**,
sem alterar critério; a pendência visual na costura/polo ortográfico permanece
em 14.05. Versão/metadata publicada permanece 0.3.0, sem publicação neste lote.


### Lote 7 — composição tipográfica internacional

**7.01–7.07 concluídos; 7.08 permanece pendente**, sem reduzir seu critério.
[Contrato, APIs, acessibilidade e políticas](international-text-0.4.md).
[Snapshot de evidências e hashes do runtime](text-validation-0.4.json).

- Runs/graphemes/scripts, direção, linguagem, fallback auditado, features
  OpenType e métricas/contornos imutáveis compartilhados. Contextos isolados;
  figuras e Artists capturam opções. Títulos, ticks, legendas, colorbars,
  annotations e labels preservam edição e visibilidade.
- Resolvedor bidi próprio a partir do UAX #9 r51, sem portar código externo.
  ICU fornece propriedades/graphemes, HarfBuzz posicionamento OpenType,
  fontTools contornos. Dependências genéricas opcionais; core e imports
  preservados. Fontes Noto opcionais OFL-1.1, bytes/hash/origem auditados;
  ausência de cobertura/permissão causa erro explícito. DejaVu inalterada.
- Conformidade oficial Unicode 15.1: **91.707 casos de caracteres, 770.241
  casos/modos por classes bidi e 1.187 casos de graphemes**, sem falhas.
  Níveis e ordem comparados integralmente, sem exceções de casos falhos.
  O resolvedor próprio corrigiu 30 divergências detectadas tanto no ICU do
  Windows 72.1.0.4 quanto no binário oficial 78.3. Esses engines não são vendorizados.
- PNG/SVG/PDF e viewers Python usam os mesmos glifos/offsets/contornos, inclusive
  no subprocesso de navegação sem registro de fontes do processo principal.
  SVG com texto lógico acessível, PDF com ActualText e avisos completos;
  não se anuncia PDF/UA nem seleção universal em todo leitor.
- Curvas conservam clusters/marcas/ligaturas; colisões, prioridades e leader
  lines usam métricas reais. Rotação/halos/DPI/caches preservados. HTML mantém
  outlines existentes e tamanho físico; recomposição arbitrária de scripts
  complexos permanece no viewer Python.
- Suíte completa: **1190 testes / 22732 subtests**, zero falhas/erros,
  três skips conhecidos; mais **3 testes de privacidade de captura**, aprovados.
  Windows/CPython 3.14.4. Tk/Qt locais capturados; Tk usa HWND e confere pixels
  antes de gravar. Recortes Linux/macOS só em runners controlados, também
  conferidos. Captura inválida não é salva; screenshots não são aceite humano.
- Workflow manual `text-review-0.4.yml` preparado, **ainda não executado na CI**.
  7.08 exige testes nos três sistemas e aprovação visual humana explícita.
  Fontes e dados Unicode opcionais são adquiridos explicitamente, fora dos archives.

Reprodução: `tests/test_text_engine_040.py`, `tests/test_text_review_tools_040.py`,
`tools/validate_unicode_text.py`, `tools/validate_text_engine.py` e
`examples/multilingual_text.py`. 2.08 continua exclusivamente pendente pelo
ensaio planetário integral; 14.05 conserva a pendência visual na costura/polo
ortográfico. Versão publicada permanece 0.3.0; sem publicação neste lote.


### Preparação do aceite 7.08

[Roteiro de revisão por plataforma](text-review-0.4.md), índices HTML,
PNG/SVG/PDF em dois DPI e capturas Tk/Qt preparados. O pacote Windows local
tem hashes conferidos; a captura Tk foi inspecionada como janela da Azimlib.
O comparador rejeita bytes alterados, runtimes/fontes divergentes e plataformas
repetidas. Execução parcial precisa de opção explícita e **nunca concede aceite**.
Os três testes desse comparador passaram em execução separada.
Linux/macOS ainda precisam gerar seus pacotes pelo workflow manual preparado;
não se registra execução remota nem aprovação humana que não ocorreu.
**7.08 continua pendente** com seu critério integral preservado.

### Lote 8 — TeX real opcional

**8.01–8.07 concluídos localmente; 8.08 pendente dos sistemas suportados.**
[Contrato e reprodução](tex-0.4.md),
[evidências/hashes do runtime](tex-validation-0.4.json) e
[fontes do ensaio](tex-fonts-reference-0.4.json).

- Tectonic 0.17.0 externo compõe fragmentos LaTeX reais; pdftocairo 26.07.0
  externo fornece contornos que a Azimlib interpreta e desenha. Matemática,
  macros, preâmbulo, métricas/baseline reais, rotação e transparência compartilham
  a cena e Artists editáveis. O parser interno continua separado.
- Configuração explícita, cache previamente preparado, runtime offline,
  diretórios temporários removidos, limites monitorados de tempo/RAM/disco e
  diagnósticos sanitizados. Executáveis/preâmbulos precisam ser confiáveis;
  monitoramento por amostragem não é sandbox nem quota rígida de kernel.
- Cache por texto/configuração/fontes/bytes das ferramentas, limitado a 128
  fragmentos e 16 MiB medidos; recursos conferidos no início e fim da composição.
  PNG/SVG/PDF/HTML e worker usam contornos preparados. Smoke do worker com
  ferramentas/cache ausentes em sua configuração produziu os mesmos pixels.
- Extra Python genérico opcional; nenhuma instalação ou aquisição implícita.
  Motor/cache/fontes não entram nos archives. Latin Modern/AMS e avisos das
  ferramentas/dependências preservados; 19 textos legais auditados. Trinta
  arquivos de fonte do cache comparados por SHA-256 com as fontes oficiais.
- Suíte completa cumulativa: **1.208 testes / 22.738 subtests**, sem falhas/erros,
  três skips conhecidos, Windows/CPython 3.14.4. Mais três testes do comparador
  7.08 em execução separada; quinze contratos TeX passaram com motor real,
  incluindo erros, timeout, glifo ausente, página extra e cache.
- Workflow manual `tex-review-0.4.yml` preparado para os três sistemas,
  **ainda não executado**. Pacote visual Windows local em 100/200 DPI;
  imagens e testes locais não encerram 8.08.

Reprodução: `tests/test_tex_040.py`, `tools/prepare_tex_cache.py`,
`tools/validate_tex.py` e `examples/tex_cartography.py`. 2.08 permanece
exclusivamente pendente pelo dump planetário completo; 14.05 conserva a pendência
visual de costura/polo ortográfico. Metadata estável permanece 0.3.0.

### Lote 9 — renderer GPU próprio e texturas

**9.01–9.07 concluídos localmente; 9.08 permanece pendente.**
[Contrato e reprodução](gpu-0.4.md),
[evidências e hashes do runtime](gpu-validation-0.4.json) e
[inventário dos bindings](gpu-dependencies-0.4.json).

- OpenGL 3.3 via ModernGL/glcontext opcionais MIT, avisos separados e 21 textos
  legais verificados. GLSL, cobertura/winding, meshes, caches, clipping,
  integração da câmera e rasterização CPU de referência são implementações próprias.
- Contexto com thread proprietária, subprocesso persistente nos viewers Tk/Qt,
  descarte de gerações obsoletas, fechamento idempotente, falha explícita e
  fallback CPU somente autorizado. Nada inicializa contexto no import.
- Cena/Artists preservados, widths/caps/joins/dashes físicos, transparência 2D,
  z-order, polígonos com furos, supersampling 3x e readback estático PNG.
  SVG/PDF mantêm os renderers vetoriais próprios; `show()` continua separado.
- Terreno/extrusões usam câmera/depth próprios, atlas combinado, UV perspectivo,
  texturas nearest opacas/mascaradas editáveis e referência CPU compartilhada.
  Transparência 3D arbitrária e volumes não são anunciados por este lote.
- HarfBuzz internacional e TeX real renderizados na GPU com os mesmos contornos
  compostos e avisos de fontes preservados. Picking usa registros originais no
  processo principal; snapshots do worker excluem metadados privados de Artists.
- Suíte cumulativa: **1.229 testes / 22.742 subtests**, zero falhas/erros,
  três skips conhecidos, Windows/CPython 3.14.4. Dispositivo real NVIDIA RTX 2060,
  driver 617.42; CPU/GPU, threads, limites, cancelamento, texturas, corrupção de
  configuração e worker concorrente cobertos. Capturas Tk/Qt conferidas.
- Caches reutilizam traduções exatas; zoom alterado recompõe meshes. Medições
  separam composição, desenho, primeira pintura e FPS sequencial. Monitoramento
  RSS separado pode perturbar os tempos; payload GPU não é RSS/VRAM total.
  As metas de 33 ms/100 ms não foram demonstradas para a interação completa.
- Workflow manual `gpu-review-0.4.yml` preparado, **sem execução remota neste
  lote**. CI sem GPU nos três sistemas e referência software Mesa/EGL são
  parte do gate 9.08, ainda aberto; capturas não constituem aceite humano.

Reprodução: `tests/test_gpu_040.py`, `tools/validate_gpu.py` e
`examples/gpu_cartography.py`. Core/imports CPU, metadata estável 0.3.0 e os
avisos de terceiros permanecem preservados. Nenhuma publicação neste lote.
2.08 permanece exclusivamente pendente pelo ensaio planetário integral;
7.08/8.08 conservam suas validações pendentes e 14.05 a revisão de costura/polo.


### Lote 10 — volumes regulares e nuvens sintéticas

**10.01–10.08 concluídos localmente no contrato declarado.**
[Guia e reprodução](volumes-0.4.md),
[evidências e hashes do runtime](volume-validation-0.4.json).

- Campos escalares/vetoriais float32 nodais Z/Y/X, coordenadas físicas XYZ,
  unidades de posição/valor, LocalFrame explícito e máscara/NoData. Arrays e
  formato próprio AZV1; sem alegar leitura de todo formato científico.
- Escrita por bricks, verificação integral SHA-256, cache LRU limitado, ROI e
  rejeição de corrupção, truncamento e alteração da fonte. O ensaio verificou
  512 bricks e 2.097.152 nós de um arquivo de 8.405.137 bytes, com teto denso de
  256 KiB e cache de 64 KiB. Pico Python medido por tracemalloc: 264.942 bytes;
  isso não mede RSS total nem VRAM. Respeitados o teto de 20 GB e a reserva de
  15 GB livres; não houve aquisição de dataset planetário.
- Integração própria por absorção/comprimento físico, transfer functions,
  Normalize/LogNorm e mistura de até quatro volumes. Cortes interpolados e
  isosuperfícies próprias por tetraedros; limites de trabalho explícitos.
- Referência Python, aceleração NumPy opcional e GLSL próprios, câmera/depth
  compartilhados com terreno, georreferência, recentering GPU, edição,
  visibilidade, picking, colorbar e vínculo temporal. PNG/SVG/PDF com volumes
  rasterizados; GIF de dois estados distintos conferido.
- Iluminação por gradiente e autoabsorção na direção da luz; modelo ilustrativo,
  sem prometer simulação meteorológica, espalhamento múltiplo ou sombras
  volumétricas projetadas por terreno. Essas distinções constam no guia.
- Suíte cumulativa final: **1.253 testes / 22.745 subtests**, sem falhas/erros,
  três skips conhecidos, Windows/CPython 3.14.4. Vinte e quatro contratos de
  volumes passaram, incluindo GPU real RTX 2060, amostragem convergente,
  alpha/depth, NoData, limites, fontes corrompidas e coordenadas grandes.
- Nuvem sintética e cortes comparados em CPU/GPU; diferenças médias da figura
  completa abaixo de 1,12/255 por canal RGB, com diferenças locais em bordas.
  Analíticos interiores têm testes de tolerância separados. Desenho GPU da
  nuvem já composta: mediana aquecida de 25,5 ms em sete amostras; não é latência
  de input/viewer nem demonstração das metas pendentes da etapa 9.
- Capturas Tk/Qt próprias verificadas e inspecionadas localmente, sem aceite
  humano multiplataforma implícito. Workflow manual GPU ampliado para volumes,
  **preparado, sem execução remota neste lote**. Nenhum dataset externo novo;
  fórmulas sintéticas originais BSD, avisos existentes de paleta/fontes/bindings
  preservados, 21 textos legais conferidos.

Reprodução: `tests/test_volume_040.py`, `tools/validate_volume.py` e
`examples/volume_cloud.py`. 2.08 continua exclusivamente pendente pelo ensaio
planetário integral; 7.08/8.08/9.08 e os gates finais da etapa 14 conservam seus
critérios. Metadata estável 0.3.0 preservada; archives são previews locais,
sem publicação, tag ou alteração de PyPI.


### Lote 11 — Sol terrestre e evidência local

**11.01–11.08 concluídos localmente no contrato de precisão declarado.**
[Modelo, fontes, correções, limites e reprodução](solar-0.4.md),
[resultados e hashes](solar-validation-0.4.json).

- Implementação analítica própria baseada nas equações publicadas pelo USNO;
  sem biblioteca de efemérides, kernel ou código externo incorporado.
- Posição geocêntrica/topocêntrica, azimute/elevação manual, paralaxe,
  aberração aproximada e refração óptica explicitamente separadas. TT/UT1
  exigem correções fornecidas pelo chamador; UTC aproximado é opção expressa.
- Ponto subsolar, terminador esférico, máscara noturna com resolução declarada,
  trajetórias diárias/sazonais em ENU 3D, solstícios/equinócios, nascer/pôr e
  trânsito. Dia/noite polar e incerteza tangente permanecem explícitos.
- Artists opcionais editáveis, visibilidade, labels com halo, picking e
  TemporalSeries/FuncAnimation; vetor físico ENU disponível para a etapa 13.
  O raio visual do céu e o símbolo não representam distâncias/tamanho reais.
- Referência independente JPL Horizons: 182 comparações angulares entre
  1972–2100, seis observadores incluindo dateline, altura e polos. Maior
  desvio 0,010299° frente ao limite pré-fixado de 0,06°; distância relativa
  máxima 0,00007806 frente a 0,0003. Doze eventos comparados com desvio
  máximo 1,810 s frente a 120 s. São resultados dessas amostras, não uma
  garantia universal de precisão; polos não têm trânsito/azimute únicos.
- Respostas brutas e tabelas JPL ficam fora do repositório e dos archives;
  evidência contém análise própria, queries e hashes. Crédito das definições
  USNO/NOAA documentado, 21 textos legais existentes preservados.
- PNG/SVG/PDF para mapa, globo e céu, CPU/GPU reais, três estados distintos
  em GIF e capturas próprias Tk/Qt verificadas. Isso não é aceite humano
  multiplataforma nem comprova as metas de latência pendentes da etapa 9.
- Suíte cumulativa: **1.281 testes / 22.765 subtests**. sem falhas/erros. 3 skips conhecidos. Os 28 contratos solares passaram.

Permanecem pendentes 2.08 (somente dump planetário completo), 7.08, 8.08,
9.08, etapas 12/13 e gates da etapa 14, com os mesmos critérios. Metadata
estável 0.3.0 preservada; nenhuma publicação, tag, push ou alteração de PyPI.


### Lote 12 — Lua e visualização Terra–Lua

**12.01–12.08 concluídos localmente no contrato declarado.**
[Modelo, API, limites e reprodução](lunar-0.4.md),
[evidência e hashes](lunar-validation-0.4.json),
[proveniência das definições](lunar-model-0.4.json).

- Série analítica curta própria, definições numéricas creditadas ao modelo
  Almanac revisado no artigo NASA de Simpson, equações 1–4; documento
  identificado pelo NTRS como trabalho governamental de uso público permitido.
  Sem código externo, kernels ou respostas/tabelas JPL incorporados.
- Posição/range geocêntricos e topocêntricos, paralaxe, refração óptica opcional,
  ponto sublunar direcional, fase e posição angular do limbo iluminado. Relógios
  TT/UT1 explícitos; UTC aproximado é opção declarada, sem tabelas inferidas.
- Artists opcionais editáveis, entrada manual de azimute/elevação com alcance
  finito/observador, labels/halo, picking geográfico e playback prevalidado.
  Trajetória calculada em frame terrestre fixo; não é uma órbita inercial.
- Corpos Terra–Lua em metros, raios/distâncias físicos por padrão, ampliação
  visual separada, câmera existente, luz baseada nos vetores físicos e
  oclusão opaca verificada CPU/GPU por reversão de câmera/ordem de faces.
  Não há sombras projetadas nem previsão de contato de eclipses nesta etapa.
- Referência independente: 792 comparações angulares, 432 distâncias/frações,
  335 orientações do limbo e 360 paralaxes, em 72 datas e cinco observadores
  além do geocentro. Máximos amostrados: 0,173591°; 653,198 km; fração 0,001358;
  limbo 0,276228° (elongação 20°…160°); paralaxe 0,002611°. Todos dentro dos
  limites pré-definidos. Não são garantias universais de erro máximo.
- Quatro cenas PNG/SVG/PDF CPU/GPU, quatro fases, três frames distintos de
  animação e capturas próprias Tk/Qt verificadas no Windows. Isso não substitui
  aceite humano nativo multiplataforma, nem metas de latência da etapa 9.
- Regressão cumulativa: **1299 testes / 22765 subtests**, zero falhas/erros e 3 skips conhecidos; 18 contratos lunares aprovados.

Permanecem pendentes **2.08** (exclusivamente ensaio planetário integral),
**7.08**, **8.08**, **9.08**, etapa **13** e gates da **14**. Critérios mantidos.
Metadata estável 0.3.0 preservada; sem push, publicação, tag ou alteração de PyPI.


### Lote 13 — iluminação física, sombras locais e geometria de fonte extensa

**13.01–13.05 e 13.08 concluídos localmente; 13.06–13.07 permanecem pendentes.**
[Contrato, API, precisão e reprodução](lighting-0.4.md),
[evidência e hashes](lighting-validation-0.4.json),
[proveniência das definições](lighting-model-0.4.json).

- Luz opcional em ENU/metres, vetor solar calculado ou direção manual explícita;
  normais/alturas físicas antes da câmera e do exagero vertical.
- BVH e interseções próprios, oclusão opaca sobre terreno/entre construções,
  refinamento de triângulos e amostragem do disco solar limitados antes da alocação.
  O exemplo usa aresta máxima 1,5 m, bias 1 mm e oito direções; bordas continuam
  dependentes da resolução, sem promessa de precisão espacial universal.
- Mudanças temporais reutilizam a geometria; câmera/exagero não alteram sombras.
  Visibilidade/material/malha invalidam o índice. Atualização temporal mantém
  a câmera existente e segue o mesmo preparo de cena CPU/GPU.
- Cones umbra/penumbra/antumbra por tangência de esferas finitas e fração de disco
  visível por aproximação angular declarada. Sem regra decorativa por evento.
  Corpos 3D e mapa escalar opcionais; ampliação visual não altera a geometria física.
- Volumes no mesmo frame recebem direção e autoatenuação já suportada; não há
  transporte de sombras entre malhas e volumes. PNG/PDF suportados; SVG incorpora
  camada raster de volume com Pillow, falhando explicitamente sem esse provider.
  Artistas removíveis/toggláveis.
- Quatro cenas originais CPU/GPU, PNG/SVG/PDF conforme capacidade, três frames
  diários distintos e capturas verificadas das próprias janelas Tk/Qt no Windows.
  Não substituem aceite humano multiplataforma nem gates de desempenho.
- **Gate real reprovado:** 96 pontos centrais independentes do eclipse NASA
  2024-04-08 não reproduzem totalidade; separação máxima 0,183489° e fração residual
  máxima 0,393908. Orçamento do modelo chega a 0,562376°, acima do limite previamente
  fixado de 0,01°. Horários de contato e eventos lunares não foram validados.
  O auditor retorna código 3; o fracasso não foi convertido em aprovação.
  **13.06 e 13.07 exigem efeméride/reduções mais precisas e validação independente
  espacial/temporal, antes do gate final.** Dados brutos NASA permanecem externos.
- Regressão cumulativa: **1322 testes / 22765 subtests**, zero falhas/erros e 3 skips conhecidos; 69 contratos de iluminação/Sol/Lua aprovados.

Pendências após o lote 13: **2.08**, **7.08**, **8.08**, **9.08**, **13.06**,
**13.07** e os gates da etapa **14**; a consolidação atual está registrada abaixo.
Metadata estável 0.3.0 preservada; sem commit, push, publicação ou tag.


### Lote 14 — integração cumulativa, auditoria e preparação da entrega

**14.01 e 14.06 concluídos localmente. Os outros seis gates permanecem pendentes.**
[Guia, cobertura e reprodução](integration-0.4.md),
[evidências e hashes](integration-validation-0.4.json),
[galeria original](gallery-0.4.md), [migração](migration-0.4.md),
[benchmarks e limites](integration-benchmarks-0.4.md),
[release notes ainda não publicadas](release-notes-0.4.0.md).

- Integração geocoder → grafo → rota → clip próprio, equivalência XML/PBF,
  roundtrip geocêntrico, topologia na costura, Sol/Lua e temporal → iluminação →
  volume no mesmo frame. Imports públicos compartilham estado; sem motor GIS externo.
- Cinco cenas originais CPU/GPU em PNG/SVG/PDF conforme capacidade e capturas
  verificadas das próprias janelas Tk/Qt Windows; core também validado sem site-packages.
- Auditoria técnica de licenças/proveniência e scans de privacidade do conteúdo,
  histórico/refs/objetos locais; termos de terceiros preservados. Não é parecer
  jurídico nem prova de apagamento remoto. Dados/fontes/referências brutos externos
  permanecem fora dos pacotes. Hashes de conteúdo distribuído verificados separadamente.
- Corrigido o gate que só exigia checklist para 0.3: 0.4 exige exatamente os 112
  IDs completos; versões sem contrato falham. Testes cobrem planeta, plataformas,
  ciência e aceite pendentes, checklist inválida e workflow sem publicação.
- **14.02:** documentação, matriz, migração e galeria prontas localmente;
  publicação/verificação pública permanece pendente.
- **14.03:** medições atuais de geodesia, topologia, PBF regional e GPU consolidadas.
  Mônaco tem relações incompletas: política estrita recusou e descarte regional
  explícito registrou 36 relações omitidas. Não constitui prova planetária.
  Faltam grandes dados reais e latência nativa ponta a ponta; composição/zoom
  ainda excedem budgets. Picos Python, RSS amostrada e VRAM não são intercambiáveis.
- **14.04:** contrato existente de 28 jobs preservado e 22 jobs adicionais manuais
  preparados para core/matrizes, ausência de providers, capturas e Mesa explicitamente
  software. Nenhuma execução remota é declarada; exigir o commit exato.
- **14.05:** aguardando revisão humana Linux/macOS/Windows; capturas automáticas
  locais não substituem interação física ou os gates 7.08/8.08/9.08.
- **14.07:** ensaio local de build/auditorias/instalação core e GPU é preliminar;
  metadata estável permanece 0.3.0, e seus arquivos não devem ser enviados ao PyPI.
  Metadata 0.4 final, commit imutável e reconstrução auditada continuam pendentes.
- **14.08:** sem aceite final, tag, Release ou publicação; nenhuma autorização
  inferida de testes locais. Ensaio planetário e precisão de eclipses ainda bloqueiam.
- Regressão cumulativa: **1334 testes / 22780 subtests**, zero falhas/erros e 3 skips conhecidos.

Pendências atuais (12): **2.08**, **7.08**, **8.08**, **9.08**, **13.06**, **13.07**,
**14.02**, **14.03**, **14.04**, **14.05**, **14.07**, **14.08**. Critérios preservados.
Sem alteração de versão estável, commit, push, tag, publicação ou download planetário.

### Checkpoint dos gates 7.08 / 8.08 / 9.08 / 13.06 / 13.07

[Resultados, artifacts por sistema e checklist visual](pending-validation-0.4.md).
7.08 e 8.08: mesma origem `d61a3ca02739ce6d8f43de175b55de75ecec58dc`,
CI 6/6, hashes/licenças/privacidade verificados; aguardando aceite visual humano.
9.08: CI 4/4 em `8959ff25c57786e487ec351bcd7615c954fbd569`; otimizações
medidas, mas budgets de 33 ms/quadro e 100 ms/interação continuam não satisfeitos.
13.06/13.07: leitor SPK/reduções experimentais e validação independente ampliada;
302 centros, 601 bordas disponíveis, 12 contatos lunares e controles sem eclipse.
2023 ainda excede os limites espaciais; orçamento global e contatos solares
absolutos permanecem pendentes. Nenhuma tolerância foi afrouxada.
2.08 continua pendente exclusivamente pelo planeta real, com protocolo preservado.
**Contagem inalterada: 100/112. Nenhum aceite automático; etapa 14 intacta.**
Snapshots de validação não são promoção da main, release ou publicação PyPI/Pages.

### Aceite visual multiplataforma — 7.08 / 8.08

Concluídos em 2026-10-12 após inspeção visual humana explícita dos artifacts
Windows, Linux e macOS: tipografia internacional e TeX multiplataforma,
PNG/SVG/PDF e capturas nativas correspondentes. Origem testada:
`d61a3ca02739ce6d8f43de175b55de75ecec58dc`, execução `38176155877`, CI 6/6.
Aprovação restrita aos dois IDs; não aprova GPU, ciência ou release.
Estado atual: **102/112**; 2.08, 9.08, 13.06/13.07 continuam pendentes.
Os registros históricos anteriores preservam o estado observado em cada rodada.
