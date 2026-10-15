# Progresso da Azimlib 0.4.0

Status: **etapa 14 em validação; candidato 0.4.0 não publicado; 14.08 não executado**.
**107 concluídos / 4 adiados / 1 pendentes de entrega ou revalidação**.
Inventário original: **112 IDs estáveis**. Escopo ativo: **107/108**; um item
permanece aberto: 14.08 — aceite final e publicação. O total histórico anterior de 102
incluía 14.01 e 14.06. A revalidação e a CI/distribuição exatas foram concluídas no SHA registrado.
Qualquer commit novo exige nova verificação antes do aceite final.

Metadata local do candidato: 0.4.0; versão publicada: 0.3.0. Esta página não constitui aceite
final, publicação ou evidência de que o candidato final passou pela etapa 14.

## Escopo, estados e rastreabilidade

- Preservar os 112 IDs e seus textos originais. [Checklist anterior, histórica](release-progress-0.4-before-rescope.md).
- [Decisão e gates adiados](deferred-gates-0.4.md), [registro estruturado](deferred-gates-0.4.json).
- GPU opcional e eclipses são experimentais nos aspectos sem demonstração;
  PBF tem validação regional real, sem comprovação planetária.
- 2.08, 9.08, 13.06 e 13.07 não foram concluídos: somente sua obrigatoriedade
  para o corte 0.4.0 foi adiada explicitamente. Budgets e tolerâncias não mudaram.
- Critérios funcionais, integridade, licenças, privacidade e regressões continuam
  obrigatórios. Falhas de gates adiados são visíveis e não viram resultados aprovados.
- 14.01 e 14.06 conservam evidência histórica separada da revalidação local atual.
  14.05 tem aceite humano explícito. CI/distribuição devem ser repetidas no
  novo SHA; 14.08 permanece aberto e exige autorização separada.
- Cada resultado pertence ao SHA testado. CI contratual de desenvolvimento não
  substitui CI completa, aceite humano ou auditoria do candidato final.
- Não usar uma contagem de conclusão integral do plano original. Ao fechar o
  escopo ativo, registrar 108 concluídos e quatro adiados dos 112 originais.
- 0.4.1: correções compatíveis; 0.5.0: Planetary Cartography / Beyond Earth;
  0.6.0: Orbits. Certificação global de eclipses não bloqueia automaticamente 0.5.0.
- Publicação, tags, Release, PyPI e documentação hospedada exigem aceite próprio;
  esta preparação não executa nenhuma dessas operações.

## Contratos de entrega

Imports root/pyplot, Artists editáveis, pontos físicos/DPI, CPU padrão e
componentes opcionais permanecem. Modelos, formatos, CRS e engines opcionais
mantêm sua cobertura declarada; familiaridade de API não significa cobertura
irrestrita. [Política de estabilidade](api-stability.md).

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
  Estado: **ADIADO** (2.08). Critério não satisfeito; [registro preservado](deferred-gates-0.4.md).

**Pendência exclusiva de 2.08: ensaio real com o dump planetário completo.**
A implementação necessária existe; PBF real menor, streaming, referências em
disco, filtros, corrupção, equivalência XML e limites de recursos já foram
validados nas [evidências por lote](#evidência-histórica-e-revalidação). Falta exclusivamente executar e validar
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
  Estado: **ADIADO** (9.08). Critério não satisfeito; [registro preservado](deferred-gates-0.4.md).
  Medições e CI contratuais históricas estão nos [resultados observados](observed-validation-0.4.md).
  Prévia rápida não demonstra os budgets do frame exato: pan, retomada e zoom
  ainda os excedem no workload registrado. CI sem GPU e Mesa não comprovam
  desempenho de GPU física ARM64, que continua sem evidência.
  Preservar o critério integral; revalidar a declaração de limites na etapa 14.

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
  Estado: **ADIADO** (13.06). Critério não satisfeito; [registro preservado](deferred-gates-0.4.md).
- [ ] **13.07** Validar eventos e limites espaciais/temporais contra fontes independentes; manter o item pendente se a precisão não sustentar o resultado anunciado.
  Estado: **ADIADO** (13.07). Critério não satisfeito; [registro preservado](deferred-gates-0.4.md).
- [x] **13.08** Integrar mapas 2D, terreno 3D, volumes quando aplicável, componentes opcionais e exportação/animação, com exemplos e inspeção visual.

## 14. Integração, validação e entrega 0.4.0

- [x] **14.01** Executar regressões integradas de urbano, CRS, topologia, geocodificação/rotas, tipografia, GPU/volumes e Sol/Lua, preservando a simplicidade da API.
- [x] **14.02** Publicar documentação e galeria reproduzível de todos os lotes, matriz de formatos/CRS/modelos/capacidades e guias de migração da 0.3.0.
- [x] **14.03** Consolidar benchmarks de datasets grandes, memória e navegação, baselines numéricas/visuais e budgets com hardware/metodologia registrados.
- [x] **14.04** Executar CI nos sistemas/Pythons suportados, cobrindo core sem extras, dependências opcionais e ausência de GPU/motores tipográficos.
- [x] **14.05** Obter validação visual humana nativa Linux/macOS/Windows e registrar o escopo de viewer, texto, 3D/volumes, navegação e exportações.
- [x] **14.06** Auditar licenças/proveniência/privacidade de código, dados, grids, efemérides, fontes, shaders, documentação e histórico; manter termos de terceiros separados.
- [x] **14.07** Preparar metadata/changelog, wheel/sdist, instalação isolada e auditorias de conteúdo/RECORD/hashes; não reutilizar resultados de outro commit.
- [ ] **14.08** Registrar aceite final do commit exato; somente com autorização explícita criar tag/Release, publicar bytes auditados, verificar PyPI, smoke limpo e documentação pública.

## Evidência histórica e revalidação

Os registros originais por lote, commits, testes e aceites permanecem na
[checklist anterior](release-progress-0.4-before-rescope.md). Não foram reescritos.
[Resultados observados](observed-validation-0.4.md) distinguem evidência de precisão/latência garantida.

### Lote 1 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 2 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 3 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 4 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 5 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 6 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 7 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 8 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 9 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 10 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 11 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 12 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 13 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md).

### Lote 14 — evidência histórica preservada

Ver [registro anterior](release-progress-0.4-before-rescope.md). Revalidação local registrada em [preparação atual](stage14-0.4.md). CI, aceite visual, artifacts finais e aceite de publicação não são inferidos desses resultados.


## Preparação atual da etapa 14

[Estado e escopo da revalidação](stage14-0.4.md). 14.02 conclui documentação e
galeria locais; o verbo original de publicação não autoriza deploy nesta rodada.
14.03 consolida somente medições existentes, sem fechar 9.08. 14.04/14.07
têm evidência anterior e serão repetidos no novo SHA; 14.05 foi aprovado e 14.08
permanece bloqueado até autorização final explícita.

## Registro operacional após a execução

[Evidência estruturada](stage14-execution-0.4.json) identifica o SHA, os dois
workflows completos e os bytes auditados. Este registro local foi escrito
após o build e não integra aqueles artifacts. Incorporar aceites/este registro
em um novo commit exige repetir CI, build e hashes antes de 14.08. Nenhum
registro posterior certifica automaticamente um SHA novo.

## Histórico: revisão visual parcial de 14.05

Escopo visual acessível aprovado nos três sistemas. TeX Windows/Linux/macOS
permanece pendente de inspeção humana. Os artifacts TeX originais do mesmo
SHA foram recuperados e seus hashes conferidos, sem regeneração. O registro
estruturado acima identifica a execução e os artifacts. 14.05 permanece aberto;
contagem inalterada: 106 concluídos, quatro adiados, dois pendentes.

O estado parcial acima é histórico e foi superado pelo aceite completo abaixo.

## Aceite visual completo e candidato pré-14.08

14.05 concluído por aceite humano explícito do material nativo Windows/Linux/macOS,
incluindo TeX recuperado das execuções originais. O aceite pertence ao candidato
`8e04017185b98bfa79d3ce43f8cc68d569441568`; [registro](visual-acceptance-0.4.json).
O candidato seguinte incorpora somente documentação/registro, sem mudança de
código funcional ou dos renders aprovados. A identidade de fonte equivalente
deve ser verificada, e CI/auditorias/pacotes devem ser repetidos no novo SHA.

Inventário original: 112 IDs; 107 concluídos, quatro formalmente adiados e um
pendente: 14.08. Escopo ativo 107/108. Não confundir candidato pronto com release
efetivamente publicada. A conclusão de 14.08 não é inferida deste aceite visual.

## Estado de publicação separado da checklist imutável

A fonte permanece em 107/108 ativos concluídos, com 14.08 desmarcado e os quatro
gates adiados intactos. O [contrato da máquina de estados](release-publication-state-0.4.md)
distingue `pending`, `authorized` e `completed`. A autorização final é versionada
em uma branch separada, após CI/build, vinculada ao SHA e hashes exatos; não é
incluída nos próprios arquivos que identifica. Preflight autorizado não conclui
14.08. Somente a evidência pós-publicação validada pode registrar 108 concluídos
operacionais, mantendo este snapshot histórico do candidato.
