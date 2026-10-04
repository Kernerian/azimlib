# Progresso verificável rumo à 0.2.0

> Evidência histórica: resultados CI, tempos e hashes abaixo pertencem aos
> snapshots originais. A preparação BSD/licenças/privacidade altera arquivos;
> os checks atuais e a relação de hashes publicados estão em
> [preparação de publicação](publication-readiness.md). Esses resultados não são uma nova execução CI.

Versão 0.2.0 em validação final de artefatos. Passos 1–4 aceitos; passo 5 aguardando build/instalação/aceite final.
As 16 frentes são o roteiro geral; não são o contador desta versão.

## Checklist completa do corte 0.2.0

Esta é a lista de execução dos **54 subpassos conhecidos deste corte**, agrupados
pelos cinco critérios. Os IDs são fixos: os próximos lotes devem informar quais
IDs avançaram e atualizar esta seção. `[x]` significa entregue com a evidência
indicada; `[ ]` significa pendente. Um item parcialmente feito permanece aberto.
Os cinco itens de aceite também entram no total, mas não são novas funcionalidades.

Fotografia de 2026-10-04: **51 concluídos / 3 pendentes**, incluindo um
aceite. A contagem será atualizada ao encerrar os próximos itens; não é uma
estimativa de esforço, prazo ou percentual de compatibilidade com Matplotlib.
Uma nova necessidade material deve entrar no registro de mudanças de escopo,
com ID e motivo, em vez de mudar silenciosamente o significado de um item.

### Passo 1 — Núcleo e edição de Artists 2D

- [x] **1.01** Manter geometrias, GeoJSON, CRS, projeções e composição próprios, sem backend geoespacial externo. Evidência: [arquitetura](architecture.md), tests/test_core.py e tests/test_datasets.py.
- [x] **1.02** Oferecer `import azimlib as azl`, subplots, séries/matrizes, data, estilos/ciclos e aliases já auditados. Evidência: [séries](series-styles.md), tests/test_series_styles.py e tests/test_style_aliases.py.
- [x] **1.03** Integrar ownership, stale, callbacks, visibilidade, remoção e clear; handles descartados não invalidam figuras antigas. Evidência: [Artists](artists.md), [lifecycle](component-lifecycle.md) e seus testes.
- [x] **1.04** Editar dados/estilos de linhas e posições/tamanhos/cores de scatter, respeitando limites manuais. Evidência: tests/test_lines_contours.py e tests/test_scatter_collection.py.
- [x] **1.05** Editar imagens escalares, meshes e vetores pelos handles existentes; compartilhar norm/cmap/clim/array com colorbars. Evidência: [campos](field-editing.md), tests/test_field_artists.py e tests/test_mappable_batches.py.
- [x] **1.06** Editar contornos por nível, rótulos individuais e cortes inline reversíveis; preservar a topologia original. Evidência: [contornos](lines-contours.md), tests/test_lines_contours.py e tests/test_contour_refinement.py.
- [x] **1.07** Prevalidar estilos numéricos, fontes, tracejados, bordas/escala/ticks e lotes selecionados; verificar sucesso/falha no Tk instalado. Evidência: [validação](artist-validation.md), 12 regressões/52 subtests e sete checks Tk.
- [x] **1.08** Fixar um catálogo de famílias/propriedades cobertas pela 0.2.0, com aliases, setters, referências e diferenças explícitas; toda a API Matplotlib não entra neste aceite. Evidência: [catálogo do corte](artist-scope-0.2.md), ligado às implementações/testes de cada família; auditoria transversal restante em 1.11.
- [x] **1.09** Auditar limites dos contornos existentes: campo constante, níveis inválidos/fora do campo, células ausentes, saddle e integração com labels/colorbar/exports; corrigir falhas encontradas e registrar diferenças da referência. Evidência: [limites](contour-boundaries.md), dez casos Matplotlib/Agg e sete regressões/44 subtests em tests/test_contour_boundaries.py.
- [x] **1.10** Validar um mapa integrado com geometria temática, scatter, mesh, vetores e contornos compartilhando normas: edição, ocultação, remoção, callback e limites manuais em PNG/SVG/Tk. Evidência: [aceite](artist-acceptance.md), seis mappables, PNG/SVG em 100/200 DPI, 14 checks Tk source/wheel e correção de imshow respeitando limites manuais.
- [x] **1.11** Auditar rejeição de propriedades/aliases não suportados nas famílias do catálogo; corrigir divergências materiais antes de editar dados ou controles e registrar limites sem prometer rollback entre vários Artists. Evidência: 28 handles auditados, aliases de bordas/getp, rejeição antecipada de alinhamento e estilos incompatíveis de texto, choropleth prevalido e referência direta em [1.11](artist-acceptance.md).
- [x] **1.12** **Aceite do passo 1:** concluir 1.08–1.11, executar regressões pertinentes e documentar limitações remanescentes do corte. Evidência: 608 testes/14.184 subtests; dez regressões novas também no wheel instalado, integração Tk source/wheel e [limites explícitos](artist-acceptance.md). Aceite deste catálogo 2D, não da API integral Matplotlib.

### Passo 2 — Layout, textos e componentes

- [x] **2.01** Compor subplots, GridSpec com spans/pesos/filhos e mosaicos aninhados. Evidência: [GridSpec](gridspec.md), [layout aninhado](nested-layout.md) e seus testes.
- [x] **2.02** Integrar tight/constrained próprios, eixos compartilhados, label_outer, insets e posições manuais. Evidência: tests/test_layout.py, tests/test_shared_axes.py e tests/test_nested_layout.py.
- [x] **2.03** Medir fontes/multilinhas e aplicar padding físico de títulos, nomes dos eixos e ticks. Evidência: [composição](sizing-composition.md), tests/test_sizing_titles.py e tests/test_text_edits.py.
- [x] **2.04** Oferecer ticks major/minor, formatos numéricos/offsets e rótulos globais editáveis. Evidência: [ticks](ticks.md), [formatação](numeric-formatting.md) e tests/test_figure_labels.py.
- [x] **2.05** Manter legenda, grid, escala, norte, rosa dos ventos, overview, colorbar e annotations opcionais; norte/rosa separados e foco do overview preto. Evidência: [componentes](components.md) e tests/test_component_lifecycle.py.
- [x] **2.06** Adaptar caixa/números/unidades da escala em tamanhos pequenos e preservar edição/visibilidade; usar halo nos labels cartográficos. Evidência: tests/test_scale_labels.py, tests/test_component_frames.py e tests/test_label_placement.py.
- [x] **2.07** Integrar colorbar vertical/horizontal, cax/barra compartilhada, legenda/atlas e componentes em 12 combinações de tamanho/DPI/orientação. Evidência: tests/test_composition_components.py e [lote integrado](larger-batch.md).
- [x] **2.08** Conferir atlas e mapa regional em figuras estreitas, fonte grande e 200 DPI: título, ticks rotacionados, supxlabel/supylabel, legenda e colorbar; ajustar colisões de layout automático mantendo posições manuais. Evidência: [24 cenas e limites](layout-acceptance.md), padding físico e [768 caixas Matplotlib/1.536 planos Python–JavaScript](text-rotation.md); 16 regressões novas source/wheel.
- [x] **2.09** Regenerar a matriz final de componentes/atlas após os ajustes; conferir PNG/SVG, toggles, resize e restauração Home no viewer instalado. Evidência: seis conjuntos PNG/SVG/HTML em 200 DPI, matriz anterior de 54 casos regenerada, 30 checks/18 frames Tk source/wheel e nove scripts anteriores repetidos no wheel; [relatórios](layout-acceptance.md).
- [x] **2.10** **Aceite do passo 2:** encerrar 2.08–2.09 e registrar casos que ainda exigem ajuste manual, conforme a distinção Matplotlib entre layout e textos posicionados livremente. Evidência: 624 testes/16.577 subtests, [limites automáticos/manuais](layout-acceptance.md), ticks fixos preservados e regras de rotação conferidas; aparência/input da janela visível continua no item 3.08.

### Passo 3 — Fidelidade visual e exportação

- [x] **3.01** Separar savefig estático de show interativo e manter toolbar/canvas próprios inspirados na referência instalada. Evidência: [viewer](viewer-validation.md), tests/test_renderers.py e smokes Tk.
- [x] **3.02** Usar fontes embarcadas, métricas e unidades físicas consistentes em PNG/SVG, incluindo rotação/halos e margens. Evidência: [qualidade](image-quality.md), tests/test_text_edits.py e tests/test_sizing_titles.py.
- [x] **3.03** Implementar traços, caps/joins, dashes, marcadores, alpha e zorder próprios, com referências selecionadas. Evidência: [estilos](style-quality.md) e tests/test_lines_contours.py.
- [x] **3.04** Implementar hachuras combináveis, repetição/densidade e recortes de áreas. Evidência: tests/test_scientific.py e tests/test_cartographic_rendering.py.
- [x] **3.05** Comparar nove pares de mapas completos e nove pares de estilos/recortes em 100/150/200 DPI. Evidência: [mapas completos](complete-map-quality.md) e [estilos](style-quality.md); isso não declara igualdade de todos os pixels com Agg.
- [x] **3.06** Corrigir strokes coincidentes sem apagar marcadores, preservando caminhos vizinhos e exportação/viewer. Evidência: 18 contratos Agg e tests/test_degenerate_strokes.py.
- [x] **3.07** Atualizar baselines finais dos exemplos Brasil/componentes, estado/foco, séries, colorbars, contornos, terreno e globo; conferir texto, marcador, stroke, clipping e ornamentos em PNG/SVG. Evidência: [38 cenas/19 exemplos](release-gallery.md), PNGs inspecionados, SVG/XML/textos/recortes e unidades compartilhadas conferidos, 19 reproduções exatas no wheel, oito pares nativos e cinco pares same-Scene/Agg; 117 regressões/2.696 subtests. Inspeção de SVG em viewer externo e Tk visível não é declarada.
- [x] **3.08** Comparar janela Tk visível com a referência Matplotlib: toolbar/ícones, canvas/margens, coordenação de cursor, fonte e comportamento de resize. Verificação visual Windows de textos/toolbar/resize/Subplots/Salvar, espessura e continuidade do pan. [Registro](viewer-visible-acceptance.md), [quatro escalas Tk](toolbar.md) e snapshot do backend aceito. não houve captura automatizada da janela.
- [x] **3.09** Corrigir diferenças materiais encontradas em 3.07–3.08 e publicar diferenças aceitas de rasterização/layout/backend. [Registro](visual-differences.md): ícones próprios, toolbar/Subplots/tooltips, redraw ao vivo de ticks com moldura fixa, espessura preservada e release perdido nas bordas. [60 gestos da referência e onze checks Tk source/wheel](pan-interaction.md); [raster temporário/processo/limites](pan-responsiveness.md). Sem equivalência completa de API, pixel ou aparência Qt.
- [x] **3.10** **Aceite do passo 3:** 3.07–3.09 encerrados com [galeria](release-gallery.md), regressões e verificação visual Windows; [diferenças explícitas](visual-differences.md). Raster preciso ainda ~1 s após soltar; desempenho detalhado, latência física medida e multiplataforma permanecem nos passos 4–5.

### Passo 4 — Desempenho e navegação

- [x] **4.01** Separar medições de preparação, composição, raster/encoding e memória, com hashes e cenários reproduzíveis. Evidência: [desempenho](performance.md) e tools/benchmark_maps.py.
- [x] **4.02** Reduzir buffers raster com tiles/bandas e cobertura própria mantendo os pixels selecionados. Evidência: tests/test_raster_buffers.py, tests/test_raster_bands.py e relatórios associados.
- [x] **4.03** Indexar/cortar geometrias cilíndricas e reusar paths projetados com retenção limitada; fallback seguro. Evidência: [índice](spatial-index.md), [paths](projected-paths.md) e seus testes.
- [x] **4.04** Integrar RGBA direto e cache limitado de vistas Tk, cópias independentes e limpeza ao fechar. Evidência: tests/test_raster_cache.py e oito checks source/wheel.
- [x] **4.05** Medir a base municipal da API IBGE (645 features/222.324 posições), quatro vistas e seis operações Tk, sem redistribuir os dados. Evidência: relatórios real-geojson-benchmark-* e [proveniência](real-geojson-provenance.json).
- [x] **4.06** Reduzir cálculos de discos/limites/áreas e verificar quatro vistas municipais sem simplificação. Evidência: [cobertura municipal](municipal-raster.md), 16 renders source e oito no wheel.
- [x] **4.07** Ampliar kernels de áreas pequenas e medir onze cenários em 100/200 DPI; integrar globo/terreno/foco/Home/resize Tk. Evidência: [kernels](stroke-kernels.md), 44 renders source, 22 wheel e 12 checks Tk.
- [x] **4.08** Perfil original de 645 municípios/892.336 posições, mesh/contornos/1.200 pontos; cobertura própria compilável opcional e LRU de paths de 16 MiB. Oito pares finais RGBA/PNG idênticos, redução local de 42–63% no raster e pan novo de 9,09 para 0,41 s na composição. [Medições e memória](performance-acceptance.md), pico WSS/commit e custo frio explícitos.
- [x] **4.09** Janela Brasil: 1.606 eventos nativos/246 pinturas idle, pan/zoom/Home/histórico e verificação visual Windows de navegação e fechamento. Janela detalhada: pan novo/retorno Home por API, canvas mapeado e pausas medidas; não é input humano. [Telemetria, latência, vistas frias/revisitadas e limites](performance-acceptance.md). Idle Tk não mede monitor/compositor; base detalhada não tem aceite de pan contínuo fluido.
- [x] **4.10** **Aceite local do passo 4:** 4.08–4.09 concluídos com [evidências reproduzíveis](performance-acceptance.md), regressões e limites de tamanho/latência/memória. Primeira preparação ainda em segundos, raster denso em dezenas de segundos e compilador opcional aumenta memória. Cache de retorno não representa primeira vista; outras plataformas permanecem no passo 5.

### Passo 5 — Validação, documentação e pacote 0.2.0

- [x] **5.01** Manter núcleo sem dependências obrigatórias e render/viewer opcionais; runtime não importa Matplotlib/GIS. Extra png: Pillow; gui: Tk + Pillow/aggdraw/NumPy genéricos para raster, sem delegar cartografia. Evidência: pyproject.toml, tools/smoke_installed_package.py e [navegação](pan-responsiveness.md).
- [x] **5.02** Incluir fontes/dados embarcados, avisos/licenças e documentação de proveniência existentes. Evidência: tests/test_distribution.py e auditoria de distribuição 0.1.0.
- [x] **5.03** Construir e auditar wheel/sdist/ZIP 0.1.0; instalar offline em ambiente novo e executar smokes Tk no wheel. Evidência: [validação](validation.md) e relatórios locais.
- [x] **5.04** Configurar CI Windows/Linux/macOS, Python 3.10–3.14 e 13 scripts desktop em 24 jobs, com logs/JSON retidos mesmo em falha. Evidência: .github/workflows/tests.yml e [guia de CI](ci-setup.md); configurado não significa executado.
- [x] **5.05** Consolidar README, instalação/extras, referências de API, exemplos/galeria e equivalências/diferenças Matplotlib → Azimlib para o catálogo final; verificar links e reprodução dos exemplos do corte. Evidência: [guia executável](getting-started.md), [catálogo de reprodução](release-gallery.md), referência de API regenerada incluindo textos/escala/projeções/EngFormatter, links locais auditados e três snippets SVG idênticos em source/core novo/gui instalado; 19 exemplos do catálogo reproduzidos no wheel sem Matplotlib/GIS. [Limites registrados](visual-differences.md).
- [x] **5.06** CI efetiva corrigida: 24/24 jobs Windows/Linux/macOS, Python 3.10–3.14, suítes instaladas/build/twine/auditoria/core, compilador e 13 scripts desktop por sistema. [Resultado remoto](ci-portability-fix.json) e [análise](release-acceptance.md). Matriz da versão promovida permanece em verificação final.
- [x] **5.07** Aceite visual/input Windows dos passos 3/4, integração Tk e limites separados por plataforma. O escopo documentado combina observação visual Windows e CI nos três sistemas. Linux/macOS tiveram Tk real oculto, sem conferência humana nativa. [Limitação explícita](release-acceptance.md).
- [x] **5.08** Reauditar nome/distribuição, dependências, assets/licenças, exclusão de dados externos e metadados deste corte. [Auditoria](distribution-acceptance.md): lookup PyPI 404 sem reserva; METADATA/extras/SPDX/RECORD, seis camadas/quatro fontes/21 ícones, arquivos exatos e twine strict. Conta/URL/publicação não configuradas; repetir nos futuros bytes 0.2.0.
- [x] **5.09** Suíte instalada core/gui e exemplos de instalação conferidos. [Resultados locais](release-validation-local.json): 675 testes por Python 3.11/3.14, skips Numba explícitos cobertos por 11 contratos/5.470 subtests; 13 scripts Tk por versão. Timeout inicial de layout retido e retry aprovado sem mudar runtime/assertions. Core offline novo, snippets SVG iguais e galeria instalada preservada; sem Matplotlib/GIS.
- [ ] **5.10** Depois dos aceites 1–4 e verificações anteriores, preparar changelog final, alterar versão para 0.2.0 e gerar wheel/sdist/ZIP correspondentes.
- [ ] **5.11** Instalar os artefatos 0.2.0 em ambiente novo e auditar conteúdo/hashes, SVG offline, PNG/Tk opcionais, exemplos e versão anunciada.
- [ ] **5.12** **Aceite do passo 5:** registrar resultados e limitações finais, fechar a checklist e declarar 0.2.0 pronta. Upload para PyPI é uma operação separada.

### Ordem de execução e mudanças de escopo

Próximo lote: **5.10–5.12**, build/instalação/aceite final dos bytes 0.2.0. **5.06–5.07** encerrados no critério explicitamente autorizado.

Escopo de plataforma em **2026-10-04**: observação visual Windows e CI nos três sistemas. A conferência física Linux/macOS fica documentada fora do aceite 0.2.0; nenhum ID foi criado/removido e testes ocultos não são descritos como input humano.

Esta seção contém todo o trabalho atualmente previsto para **este corte**,
não todo o inventário de crescimento. Urbano (cidades/bairros/ruas/construções),
3D/tempo, Qt, novos formatos, transformações completas, MathText/TeX e demais
expansões seguem [as 16 frentes](pending.md) após a 0.2.0. Não passam a bloquear
esta versão por aparecerem naquele inventário. Nenhum subpasso novo foi
acrescentado desde a criação desta checklist; adições terão ID, data e motivo.

Lotes de 2026-10-03: concluídos **1.08–1.12, 2.08–2.10, 3.07–3.10, 4.08–4.10, 5.05 e 5.08–5.09**. Campo constante, contornos,
catálogo, integração de seis camadas e propriedades/aliases documentados e
verificados; passos 1–4 aceitos no escopo. Suíte completa atual: **675 testes / 22.192
subtests**, sem falhas. O lote da toolbar/editor acrescentou sete regressões/23 subtests;
widgets reais comparados em quatro escalas Tk, 28 checks source/wheel e correções
de Pan/Zoom, hover, ícones, Subplots e cursor. A conferência visual Windows está registrada em [3.08](viewer-visible-acceptance.md). O lote visual/documentação repetiu 117 dos testes anteriores
(2.696 subtests), sem falhas; não são testes adicionais à suíte. Os três itens
abertos incluem um aceite; os dois
restantes são subpassos de trabalho/verificação, sem relação com as 16
frentes do roteiro futuro. Para auditar IDs, totais e
links locais: `python tools/check_release_progress.py` na raiz do projeto.

## Subpassos recentes encerrados

| Subpasso | Estado | Evidência |
|---|---|---|
| Validar/normalizar estilos numéricos e fontes antes de editar o conjunto auditado de Artists | Concluído no escopo documentado | tests/test_artist_validation.py, docs/artist-validation-reference.json |
| Garantir tracejados próprios estáveis e edições prevalidadas de bordas/escala/ticks | Concluído no escopo documentado | 12 regressões/52 subtests do lote, suite cumulativa |
| Integrar sucesso/falha de edições combinadas com Tk e exportação | Concluído localmente | sete verificações reais Tk source/wheel, exemplo antes/depois PNG/SVG/HTML |
| Resolver aliases antes dos defaults e rejeitar grafias ambíguas no conjunto auditado | Concluído no escopo selecionado | 13 pares registrados de Matplotlib, tests/test_style_aliases.py |
| Combinar componentes opcionais, atlas e colorbar em tamanhos/DPI/orientações diferentes | Concluído nos cenários selecionados | matriz de 12 combinações + visibilidade, norm, posições e exports em tests/test_composition_components.py |
| Reusar raster de vistas visitadas no Tk com retenção limitada e pixels preservados | Concluído localmente | tests/test_raster_cache.py; oito verificações Tk source/wheel |
| Medir dados municipais reais com equivalência de índice/cenas/PNG e navegação | Concluído na base da API descrita | 645 municípios/222.324 posições; quatro vistas e seis operações Tk; relatórios real-geojson-benchmark-* |
| Reduzir cálculos repetidos na cobertura de discos/limites/áreas sem simplificar a geometria | Concluído no escopo medido | quatro vistas, 16 renders RGBA/PNG idênticos; tests/test_municipal_stroke.py; docs/municipal-raster.md |
| Ampliar kernels de áreas pequenas preservando a ordem/bits da soma | Concluído no escopo auditado | tests/test_stroke_kernels.py; onze cenários/44 renders em 100/200 DPI |
| Corrigir traços totalmente coincidentes sem interferir em marcadores | Concluído nos casos selecionados | 18 contratos Agg, tests/test_degenerate_strokes.py; PNG/SVG e edições no Tk |
| Integrar globo/terreno, foco/Home e 200 DPI com raster/exportação estática | Concluído localmente | 12 verificações source/wheel em tools/smoke_stroke_kernels_tk.py; nono script CI configurado |

Esses subpassos não prometem a API integral, parsing completo de cores/fontes,
transação entre vários Artists ou comportamento idêntico em todas as plataformas.
Limites: [auditoria de Artists](artist-validation.md).

## Estado dos cinco critérios

1. **Artists: aceito** no [catálogo 2D](artist-scope-0.2.md), com
   [integração, auditoria e limites](artist-acceptance.md). Expansões da API
   permanecem no roteiro futuro, sem reabrir o corte por inferência.
2. **Composição: aceita** nos [cenários e limites](layout-acceptance.md): textos,
   componentes/atlas, 200 DPI, posição manual, toggles/resize/Home source/wheel.
3. **Visual: aceito** no corte, com [galeria](release-gallery.md), correções e
   [verificação visual Windows](viewer-visible-acceptance.md); diferenças de
   raster/fontes/toolkit registradas, sem equivalência pixel a pixel.
4. **Desempenho: aceito localmente** com [base original/camadas, input humano, pintura Tk e limites](performance-acceptance.md). Pixels preservados, composição de pan novo acelerada e raster opcional próprio compilado; não promete rapidez arbitrária, latência do monitor ou outras plataformas.
5. **Release:** CI efetiva aprovada nos três sistemas; aceite visual Windows e limites nativos Linux/macOS explícitos, no escopo de plataforma documentado. Build/instalação 0.2.0 em verificação final.

Este registro complementa [os critérios](release-0.2.md); não os substitui.
Urbano, 3D, Qt e novos formatos ficam depois. Não há percentual/data estimados;
novos subpassos só serão encerrados com evidência. Publicação PyPI é separada.

Lote maior de 2026-10-02: [entregas, reprodução e limites](larger-batch.md).
Suíte cumulativa atual: 675 testes/22.192 subtests. O lote de consolidação
acrescentou 21 regressões/61 subtests e oito verificações Tk source/wheel;
o lote seguinte de [cobertura municipal](municipal-raster.md) acrescentou
quatro regressões/1.087 subtests e repetiu os oito scripts Tk no wheel instalado.

O [lote de contornos e integração](stroke-kernels.md) acrescentou oito
regressões/5.887 subtests, 18 contratos Agg e 12 novas verificações Tk
source/wheel; os oito scripts anteriores passaram novamente no wheel.
