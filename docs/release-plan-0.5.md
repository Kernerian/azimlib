# Checklist de desenvolvimento — Azimlib 0.5.0

Estado: **Fase A implementada e validada localmente**, sem publicação.
Inventário preservado: **122 IDs** (19 frentes + etapa transversal).
**17/122 concluídos; 105 abertos**, incluindo implementações parciais.
Os resultados locais não equivalem à matriz multiplataforma/aceite final da release.
Evidência e limites: [registro da Fase A](foundation-validation-0.5.md).

Fonte de escopo: [proposta consolidada](proposal-0.5.md). Os seis subitens de
cada frente decompõem contrato, implementação futura e evidência; as descrições
completas e requisitos da proposta são normativos para esta lista, não opcionais.
Os IDs desta lista pertencem exclusivamente à 0.5.0: nunca substituem os IDs
adiados da 0.4.0. Evidências futuras devem identificar versão + ID + SHA.

## 1 — Modelo público de corpo celeste

- [x] 1.01 — Definir Body público: identidade, formas, eixos, meridiano, orientação, convenções, imutabilidade e validação de parâmetros.
- [x] 1.02 — Especificar esfera/elipsoide/triaxial e malha irregular explícita; matriz de operações suportadas e recusas, sem fallback esférico oculto.
- [x] 1.03 — Preparar presets Terra/Lua/Marte/Vênus/Mercúrio com constantes, modelo, fonte, versão, unidade e domínio.
- [x] 1.04 — Definir registro/extensão para luas, planetas anões, asteroides e modelos fornecidos, sem download implícito.
- [x] 1.05 — Migrar o Body interno para a fundação pública sem regressão dos defaults e objetos terrestres existentes.
- [x] 1.06 — Validar identidade, invariantes de formas, entradas inválidas, presets e fixtures independentes; registrar capacidades não demonstradas.

## 2 — Coordenadas e referenciais planetários

- [x] 2.01 — Fixar contrato planetocêntrico/planetográfico, altura, longitude positiva/intervalo, unidades e polos por modelo.
- [x] 2.02 — Representar Body, datum, época, frame e orientação sem inferência terrestre em dados planetários.
- [x] 2.03 — Implementar as transformações suportadas e inversas, com consistência de eixos/unidades e erros explícitos para combinações inválidas.
- [ ] 2.04 — Integrar contexto de coordenadas a datasets/leitores; dados GeoJSON não terrestres exigem declaração explícita sem redefinir o padrão externo.
- [x] 2.05 — Preservar tempos/recusas existentes; documentar dados, relógios e validade exigidos por novas orientações dependentes do tempo.
- [x] 2.06 — Validar roundtrips, polos, emendas e conversões contra referências independentes, fixando tolerâncias antes da avaliação.

## 3 — Projeções e geodésia por corpo

- [ ] 3.01 — Fixar matriz de projeções globais/regionais/polares e planificação global, superfícies e singularidades, preservando fórmulas terrestres válidas.
- [ ] 3.02 — Implementar projeção/inversa Body-aware com clipping de horizonte, polos, antimeridiano e domínios declarados.
- [ ] 3.03 — Integrar distância, azimute, rotas geodésicas, comprimento e área para modelos demonstrados; unidades físicas explícitas.
- [ ] 3.04 — Preparar perfil de elevação entre pontos com datum vertical, resolução, amostragem, NoData e exagero separados de distância real.
- [ ] 3.05 — Investigar geodésia/área/inversas triaxiais e irregulares e planificação de malhas; documentar método, limites e pesquisa não encerrada.
- [ ] 3.06 — Validar casos independentes e adversos por modelo, sem aprovar operações não demonstradas ou chamar troca de raio de generalização universal.

## 4 — Raster, imagens e relevo extraterrestre

- [ ] 4.01 — Definir raster Body-aware, georreferência, resolução, unidades, datum vertical, máscaras/NoData e origem de pixels.
- [ ] 4.02 — Integrar DEMs, imagens orbitais e mosaicos com resampling/máscaras e leitura delimitada por recursos.
- [ ] 4.03 — Estender texturas, relevo 2D/3D, hillshade e exagero vertical, preservando a superfície e o dado original.
- [ ] 4.04 — Suportar corpo inteiro → região → feição → terreno local com eixos/escala consistentes e cobertura explicitada.
- [ ] 4.05 — Preparar fixtures e aquisição opcional verificável de dados licenciados, recusando mistura incompatível de Body/datum.
- [ ] 4.06 — Validar mosaicos, polos, emendas, NoData, perfis e exportação; quantificar diferenças de resolução/interpolação.

## 5 — Feições e cartografia geológica

- [ ] 5.01 — Definir atributos genéricos de crateras, vulcões, montanhas, cânions, mares, calotas, falhas e regiões nomeadas.
- [ ] 5.02 — Representar geometrias e nomenclatura com língua, fonte, validade e incerteza sem acoplar dados a presets visuais.
- [ ] 5.03 — Integrar unidades geológicas, categorias, hatches/padrões, máscaras e legendas às primitivas comuns.
- [ ] 5.04 — Integrar símbolos e labels de feições com prioridades, filtros por escala e interação.
- [ ] 5.05 — Preparar mapas geológicos/exploratórios Lua/Marte/Vênus e cobertura dos presets iniciais com dados sintéticos ou licenciados.
- [ ] 5.06 — Validar georreferência, nomenclatura, unidades e consistência visual com o mesmo conjunto de Artists usado na Terra.

## 6 — Iluminação planetária

- [ ] 6.01 — Definir origem da luz, relógios, orientação, frame, normais, horizonte e validade científica por Body.
- [ ] 6.02 — Estender iluminação, terminadores e incidência para modelos suportados com dados/referências próprios.
- [ ] 6.03 — Integrar relevo, sombras e exagero visual, distinguindo superfície física de apresentação.
- [ ] 6.04 — Definir modelos atmosféricos opcionais somente onde dados/física sustentarem contrato e limites claros.
- [ ] 6.05 — Integrar tempo e playback sem extrapolar silenciosamente efemérides/orientação nem promover eclipses experimentais.
- [ ] 6.06 — Validar iluminação/terminador/incidência contra casos geométricos e referências independentes, com tolerâncias predefinidas por domínio.

## 7 — Exploração e evolução temporal

- [ ] 7.01 — Representar locais de pouso, trilhas/waypoints de rovers, regiões exploradas e instrumentos sem API planetária paralela.
- [ ] 7.02 — Integrar rotas científicas/travessias de superfície com caminhos editoriais, geodésicos e de rede explicitamente diferenciados.
- [ ] 7.03 — Representar observações temporais de calotas, poeira e iluminação com fonte, época, validade e unidade.
- [ ] 7.04 — Integrar animação/playback, picking e atualizações de camadas aos mecanismos existentes.
- [ ] 7.05 — Separar medição, reconstrução, planejamento, interpolação visual e previsão; não produzir trajetórias orbitais implícitas.
- [ ] 7.06 — Validar sequências reproduzíveis, ausência de dados, limites temporais, lifecycle e exportações de cenas de exploração.

## 8 — Comparação entre mundos

- [ ] 8.01 — Definir comparação com escala física versus normalização visual, unidades e exageros identificados.
- [ ] 8.02 — Compor corpos distintos na mesma Figure/SubFigure com contextos isolados e interface comum.
- [ ] 8.03 — Integrar comparação corpo/região/feição/terreno e vistas global/polar sem escala enganosa.
- [ ] 8.04 — Integrar insets e legendas às vistas comparativas, sem converter locators entre corpos distintos automaticamente.
- [ ] 8.05 — Preparar exemplos comparativos com dois ou mais presets iniciais e mesma linguagem de Artists.
- [ ] 8.06 — Validar independência de contexto, estilos, escalas, interação e exportação de layouts comparativos.

## 9 — Integração com a API existente

- [x] 9.01 — Definir propagação de Body e contexto em Figure/Axes/Artists, com defaults terrestres e propriedade explícita dos dados.
- [ ] 9.02 — Integrar scatter, linhas, raster, terreno, labels, escalas e dados GeoJSON contextualizados ao Body ativo.
- [x] 9.03 — Preservar lifecycle, ownership, stale/invalidação, callbacks, picking e remoção de objetos.
- [x] 9.04 — Preservar CPU padrão, dependências opcionais e imports raiz/pyplot; documentar mudanças públicas e migração.
- [x] 9.05 — Fixar matriz de API/capacidades/erros explícitos, distinguindo suportado, experimental, pesquisa e não implementado.
- [x] 9.06 — Executar regressão Terra e testes de isolamento entre corpos/projeções/layouts sem criar segundo sistema de plotting.

## 10 — Dados, precisão e proveniência

- [ ] 10.01 — Inventariar fontes de constantes, modelos, datasets, imagens, símbolos, fontes tipográficas e exemplos; preservar direitos/avisos.
- [ ] 10.02 — Registrar origem, edição/data, hash, frame/datum/época, unidade, licença e domínio por material externo.
- [ ] 10.03 — Preparar fixtures sintéticas/reais reproduzíveis e aquisição opcional com consentimento explícito, limites de recursos e integridade.
- [ ] 10.04 — Fixar antes dos testes corpus independente, tolerâncias e critérios por grandeza/modelo; sem claims científicos universais.
- [ ] 10.05 — Integrar relatórios de erro, limitações, casos adversos, domínio e recusas à documentação de cada capacidade.
- [ ] 10.06 — Auditar licenças, assets, metadados/privacidade e registros de precisão sem reescrever evidência dos quatro gates adiados da 0.4.0.

## 11 — Símbolos e ícones cartográficos georreferenciados

- [ ] 11.01 — Definir símbolo georreferenciado genérico, catálogo/categorias e ownership como Artist compatível, válido em qualquer Body.
- [ ] 11.02 — Suportar símbolos nativos, marcadores vetoriais, SVG customizado delimitado, PNG/imagens externas e símbolos do usuário com proveniência.
- [ ] 11.03 — Integrar tamanho visual/mapa, rotação, alpha, zorder, ancoragem, offsets, clipping e prioridade visual sem distorção pelo viewport.
- [ ] 11.04 — Integrar labels associados, picking e legenda automática/explícita com amostras coerentes de ícones/categorias.
- [ ] 11.05 — Preparar recursos/portos/cidades/fortalezas/batalhas/minas/templos e pousos/sondas/rovers/bases/instrumentos/pontos científicos na mesma infraestrutura.
- [ ] 11.06 — Validar SVG seguro/limitado, assets inválidos, direitos, proporções e edição/exportação Terra/Marte/Lua; rejeitar recursos não suportados explicitamente.

## 12 — Regiões e áreas temáticas personalizadas

- [ ] 12.01 — Definir áreas independentes de limites administrativos, Polygon/MultiPolygon e conjuntos de geometrias com Body explícito.
- [ ] 12.02 — Integrar preenchimento, alpha, contorno, hatches/padrões, máscaras, sobreposição e prioridade de desenho.
- [ ] 12.03 — Integrar label central/calculado, clipping geográfico, antimeridiano, polos/horizonte e diversas projeções.
- [ ] 12.04 — Oferecer área binária, polígonos discretos, bandas/degraus e gradiente matematicamente definido como escolhas explícitas.
- [ ] 12.05 — Documentar núcleo/controle/influência/fronteira aproximada/alcance provável como semânticas externas; nunca inferir heatmap ou probabilidade.
- [ ] 12.06 — Validar furos, componentes, interseções, continuidade de padrões e efeitos por projeção em regiões históricas/sintéticas e geológicas planetárias.

## 13 — Rotas, fluxos e curvas cartográficas

- [ ] 13.01 — Separar contratos editorial, geodésico, rede/grafo e trajetória física reservada à 0.6.0; declarar espaço de interpolação e unidades.
- [ ] 13.02 — Integrar polilinhas, waypoints, curvas suaves, Bézier, splines, arcos geodésicos e paths explícitos do usuário.
- [ ] 13.03 — Suportar setas/direção, largura, cor, alpha, tracejado e fluxos proporcionais com unidade e legenda explícitas.
- [ ] 13.04 — Posicionar símbolos e labels ao longo do caminho com clipping, offsets e efeitos visuais sem mudar a geometria científica.
- [ ] 13.05 — Integrar usos comerciais/migração/expedições/campanhas/ferrovias/marítimos/econômicos e rotas de rover/superfície com a mesma API.
- [ ] 13.06 — Validar continuidade, antimeridiano, horizonte, medida original preservada, proporção de setas e determinismo sob projeção/zoom/exportação.

## 14 — Inset maps, minimapas e locator maps

- [ ] 14.01 — Estender insets existentes para múltiplos Axes com posição, tamanho, moldura, background, projeção, Body e viewport próprios.
- [ ] 14.02 — Definir footprint retangular/poligonal, destaque de região e máscara externa ao foco com geometria real entre projeções.
- [ ] 14.03 — Integrar linhas de conexão opcionais, clipping, antimeridiano, polos/horizonte e oclusão de locators.
- [ ] 14.04 — Implementar sincronização opcional unidirecional/bidirecional explícita, evitando ciclos, recursão e vazamento de estado.
- [ ] 14.05 — Preparar mundo/região/detalhe, Marte/Jezero, Lua/Apollo, polo/global e corpo/terreno; corpos distintos exigem correspondência explícita para locator.
- [ ] 14.06 — Validar pan/zoom/resize, independência de viewport/Body, grupos reutilizados, lifecycle, composição e exportação dos insets.

## 15 — Composição cartográfica editorial

- [ ] 15.01 — Definir legendas heterogêneas de linhas/áreas/ícones/símbolos com grupos/seções, handles automáticos e explícitos.
- [ ] 15.02 — Integrar título/subtítulo, caixas explicativas, notas e fontes/proveniência como elementos editáveis de layout.
- [ ] 15.03 — Integrar escala gráfica, rosa dos ventos, indicador norte/orientação, molduras e neatlines com semântica adequada ao Body/projeção.
- [ ] 15.04 — Compor mapa, legenda, notas e múltiplos insets com limites, prioridades e posicionamento automático/manual determinístico.
- [ ] 15.05 — Preservar decoração opcional separada da geometria e edição externa via SVG/PDF sem exigir editor para operações básicas.
- [ ] 15.06 — Validar página de atlas/didática completa, toggles, resize/DPI, espaçamento, orientação rotacionada e escala local declarada.

## 16 — Labels e anotações cartográficas avançadas

- [ ] 16.01 — Unificar candidatos de pontos, áreas, linhas e curvas com baselines explícitas/calculadas e sem alterar geometria dos dados.
- [ ] 16.02 — Integrar rotação, halo, outline, background, callouts, leader lines e offsets manuais/automáticos.
- [ ] 16.03 — Integrar prioridade, colisões, exclusão seletiva, obstáculos de símbolos/insets/legenda e orçamento de recursos determinístico.
- [ ] 16.04 — Definir regras por escala, repetição/único, nomes extensos atravessando regiões e estabilidade visual sob pan/zoom.
- [ ] 16.05 — Preservar shaping internacional, clusters e fallback explícito; documentar limites de texto curvo/math/TeX sem deformar scripts.
- [ ] 16.06 — Validar textos multilíngues, regiões grandes, curvas adversas, omissões justificadas e exportações, com possibilidade de override manual.

## 17 — Camadas temáticas e grupos

- [x] 17.01 — Definir extensão de Artist/Layer para grupos sem hierarquia incompatível ou ciclos, com propriedade/lifecycle explícitos.
- [ ] 17.02 — Integrar visibilidade e zorder de grupos, clipping comum e estilos compartilhados com precedência documentada.
- [ ] 17.03 — Definir inclusão/exclusão de grupos na legenda e tratamento dos labels/símbolos associados.
- [ ] 17.04 — Reutilizar dados/definições em layouts/insets com instâncias por viewport, sem anexar o mesmo Artist mutável a múltiplos Axes.
- [ ] 17.05 — Integrar picking, callbacks, redraw/invalidação e remoção com renderização interativa e caches seguros.
- [ ] 17.06 — Validar grupos aninhados, clipping, estilos, toggles e isolamento entre corpos/layouts, incluindo ausência de vazamentos de estado.

## 18 — Estilos temáticos reutilizáveis

- [ ] 18.01 — Definir tema cartográfico configurável/extensível e precedência entre defaults, contexto, grupos e edição individual.
- [ ] 18.02 — Cobrir fronteiras, água, terreno, labels, cidades, rotas, símbolos, legenda e inset sem inserir dados no estilo.
- [ ] 18.03 — Preparar presets opcionais atlas, histórico, político, físico, científico, geológico e exploração planetária.
- [ ] 18.04 — Preservar API granular, escolhas explícitas e aplicação a qualquer Body sem pressupor oceanos/continentes terrestres.
- [ ] 18.05 — Integrar temas a legendas/categorias e composição, com contraste/legibilidade e autoria/licenças de assets documentados.
- [ ] 18.06 — Validar escopo de contextos, edição/reversão, ausência de dados embutidos e consistência de temas Terra/Lua/Marte.

## 19 — Exportação editorial e composição multiplataforma

- [ ] 19.01 — Fixar matriz de capacidades das novas primitivas por PNG/SVG/PDF, distinguindo vetores, outlines, texto semântico e raster declarado.
- [ ] 19.02 — Preservar vetores SVG quando possível para texto, rotas, áreas, símbolos, molduras e insets, sem rasterização silenciosa da página.
- [ ] 19.03 — Integrar dimensões/páginas, DPI, unidades físicas, embedding/fontes, transparência, blending e efeitos suportados com fallback explícito.
- [ ] 19.04 — Validar clipping, padrões/hatches, imagens, símbolos, fontes e composição de insets nos backends correspondentes.
- [ ] 19.05 — Executar matriz Windows/Linux/macOS com mesmos workloads e registro de versão, SHA, dependências/fontes e resultados por backend.
- [ ] 19.06 — Gerar artifacts comparáveis e exigir aceite visual humano dos formatos/plataformas, sem prometer identidade pixel a pixel universal.

## 20 — Integração, exemplos e futura entrega (etapa transversal)

- [ ] 20.01 — Executar a regressão integrada Terra/Bodies e contratos de lifecycle, CPU/fallback, erros, formatos e dependências opcionais no mesmo SHA.
- [ ] 20.02 — Criar `examples/thematic/historical_trade_map.py`: região, territórios, cidades, recursos, rotas curvas, labels, legenda mista, orientação e locator, com dados próprios/públicos/sintéticos documentados.
- [ ] 20.03 — Criar `examples/planetary/mars_exploration_map.py` com geologia, rover, waypoints e minimapa, demonstrando as mesmas primitivas do exemplo terrestre.
- [ ] 20.04 — Completar exemplos Lua/mares/crateras/pousos/inset, Vênus/raster/regiões/símbolos e comparação com Mercúrio; verificar polos e escalas.
- [ ] 20.05 — Consolidar API, migração, galeria, limites científicos, capacidades/recusas, proveniência e resultados reais de benchmarks sem herdar metas GPU como garantias.
- [ ] 20.06 — Auditar licenças, assets, privacidade, datasets e preservação dos quatro gates adiados da 0.4.0; nenhuma evidência histórica reescrita.
- [ ] 20.07 — Preparar CI exata, pacotes, hashes, instalação isolada e revisão humana final futura, distinguindo candidato técnico de publicação concluída.
- [ ] 20.08 — Publicar somente com autorização explícita futura; exigir estados pending/authorized/completed e evidência pós-publicação sem dependência circular.

## Regras de contagem e fechamento futuro

A contagem distingue os 17 subitens demonstrados dos 105 ainda abertos.
Interfaces preparadas, recortes ou exemplos parciais não concluem frentes inteiras.
As descrições originais dos 122 critérios permanecem preservadas.
Não transportar os quatro adiamentos da 0.4.0 como quatro itens aprovados,
nem ocultá-los na contagem da 0.5.0. Suas identidades continuam **0.4.0/2.08**,
**0.4.0/9.08**, **0.4.0/13.06** e **0.4.0/13.07**, no registro original.

Antes de cada fase seguinte, revisar contratos, domínios científicos e viabilidade
dos subitens de pesquisa. Qualquer adiamento futuro precisa de decisão explícita,
critério/evidência preservados e contagem distinta de entregue/adiado/pendente.
Não promover operação irregular/triaxial ou previsão científica sem demonstração.
Nada neste plano autoriza modificar os pacotes da 0.4.0, iniciar a etapa 14 antiga,
publicar site, criar nova tag/Release ou enviar arquivos ao PyPI.

## Evidência da Fase A e progresso parcial

As marcações acima referem-se aos contratos estáticos delimitados em
[foundation-0.5.md](foundation-0.5.md), testes
`test_planetary_foundation_050.py`, `test_groups_050.py`,
`test_foundation_examples_050.py` e regressão integrada local.
SHA, contagens, corpus e formatos estão no registro de validação.

Continuam abertos, com progresso parcial:

- **2.04**: wrapper PlanetaryData/leitor GeoJSON explícito; raster e outros
  datasets planetários ainda não integrados.
- **8.01/8.02/8.05/8.06**: dois contextos na mesma Figure e exemplo sintético
  angular; comparação física, todas as vistas e aceite multiplataforma futuros.
- **9.02**: linhas/scatter/texto/geometrias angulares; raster, terreno e escala
  métrica fora da Terra são recusados, não implementados.
- **10.01–10.06**: fontes das constantes/fixtures, tolerâncias prévias e auditoria
  local desta fundação; inventário/corpus dos recursos posteriores continuam abertos.
- **17.02**: visibilidade, offsets de zorder, defaults de estilos e clip retangular
  reais; clipping geográfico/poligonal comum continua futuro.
- **17.03**: sem política de legenda seccional/inclusão de grupos nesta fase.
- **17.04**: instâncias independentes apenas de Layer geométrico simples;
  clonagem de coleções especializadas/dados futuros continua recusada.
- **17.05/17.06**: picking de folhas, callbacks, stale, serial de cache,
  remoção/toggles e isolamento testados localmente; cobertura editorial completa
  e interação nativa multiplataforma permanecem abertas.
- **20.01/20.05/20.06/20.07**: regressão, guia, auditorias e pacotes privados
  dev desta fase não substituem validação integrada final da 0.5.0.

Demais frentes continuam planejadas; nenhuma Fase B–F foi concluída por analogia.
