# Escopo e aceite de Azimlib 0.2.0

> Evidência histórica: resultados CI, tempos e hashes abaixo pertencem aos
> snapshots originais. A preparação BSD/licenças/privacidade altera arquivos;
> os checks atuais e a relação de hashes publicados estão em
> [preparação de publicação](publication-readiness.md). Esses resultados não são uma nova execução CI.

A versão 0.2.0 está pronta no corte documentado; [aceite e limites](release-acceptance.md). O inventário possui **16 frentes de
trabalho**, cada uma com várias tarefas; não representa 16 alterações pequenas
nem um número fechado de funcionalidades futuras. Consulte [pendências](pending.md).
Entregas dentro de uma frente reduzem seu trabalho pendente sem mudar esse total.
Índice espacial/cache de paths e lotes editáveis de cores já são entregas concluídas.

0.2.0 consolida o núcleo cartográfico 2D e a experiência familiar de Matplotlib.
Os cinco critérios abaixo estão aceitos no escopo registrado. Novos formatos,
3D, backend Qt e compatibilidade integral fazem parte do roteiro futuro.

A execução segue a [checklist completa](release-progress.md): IDs fixos,
concluídos/pendentes e evidências por passo. As 16 frentes de crescimento não
substituem essa lista nem seu contador. [Catálogo](artist-scope-0.2.md) e
[limites de contornos](contour-boundaries.md) detalham os itens 1.08–1.09.

Decisão de escopo: **cartografia urbana fica para depois da 0.2.0**, junto
da fundação 3D e das demais expansões fora deste corte. O trabalho atual
consolida os recursos 2D existentes; não inicia essas expansões para fechar 0.2.

Os relatos de lotes e pendências intermediárias nesta página são históricos;
o estado final é a checklist 54/54 e o aceite atual abaixo.

Lote maior de 2026-10-02: aliases auditados, composição com componentes em
doze cenários adicionais, cache limitado de raster no Tk e medição da API
municipal real. São subpassos concluídos no [registro](release-progress.md),
com [evidências e limites](larger-batch.md). Primeira rasterização densa,
apresentação física/input nativo e CI efetiva continuam abertos.

O lote seguinte de [cobertura municipal](municipal-raster.md) reduz cálculos
repetidos em vistas novas, com RGBA/PNG preservados na comparação local.
É avanço incremental do quarto critério, que continua parcial.

O [lote de contornos e integração](stroke-kernels.md) acrescenta kernels de
área preservando aritmética/pixels, corrige linhas coincidentes com marcadores
independentes e verifica globo/terreno em Tk/exports/200 DPI. Onze cenários de
raster e 12 verificações desktop novas ampliam a evidência local; os cinco
critérios permaneciam parciais naquele lote.

**Estado atual:** passo 1 aceito no [catálogo](artist-scope-0.2.md), após
integração de seis mappables, auditoria de propriedades/aliases e 608 testes/
14.184 subtests. [Aceite 1.10–1.12](artist-acceptance.md), com 14 checks Tk
source/wheel e limites explícitos. Passo 2 também aceito em [2.08–2.10](layout-acceptance.md):
24 cenas de layout, rotação/padding, componentes e 30 checks Tk source/wheel;
suíte registrada no lote de navegação e
[verificação visual do passo 3](viewer-visible-acceptance.md).
Passo 4 também aceito localmente: [base original, raster compilado próprio opcional e input humano](performance-acceptance.md), com limites explícitos. CI corrigida 24/24 e critério de plataforma documentado encerram 5.06–5.07. Checklist: **54 concluídos/zero pendentes**. [Matriz da versão](ci-0.2.0.json), [instalação isolada](release020-local-validation.json) e auditoria dos artefatos concluídas. Baselines finais e
[documentação executável](release-gallery.md) encerram 3.07/5.05, com 38 cenas,
19 reproduções exatas no wheel e 117 regressões selecionadas repetidas.

| Critério de conclusão | Entregue nesta fundação | Trabalho necessário para fechar 0.2 |
|---|---|---|
| 1. Edição coerente de Artists 2D | Catálogo e limites de contornos auditados; seis mappables em cenário integrado; aliases/rejeições em 28 handles; controles, callbacks, edição, visibilidade, remoção e exports/Tk verificados | **Aceito no catálogo 2D**, conforme [1.10–1.12](artist-acceptance.md). Expansões da API e diferenças explícitas não reabrem este corte por inferência |
| 2. Composição familiar | GridSpec raiz/filhos/spans/pesos, tight/constrained próprios, eixos compartilhados, insets, barras/cax e rótulos globais; 24 cenas, fontes grandes/200 DPI, regras de rotação/padding e toggles/resize/Home source/wheel | **Aceito no escopo documentado**, conforme [2.08–2.10](layout-acceptance.md); textos livres/posições manuais e diferenças de solvers permanecem explícitos |
| 3. Qualidade de PNG/SVG | antialiasing próprio, métricas/fontes, pontos físicos, hachuras, pares de mapas/estilos; baselines de 19 exemplos em 100/200 DPI e viewer corrigido | **Aceito no corte**, 3.08–3.10: [observação visual Windows](viewer-visible-acceptance.md), regressões e [diferenças explícitas](visual-differences.md) |
| 4. Desempenho medido | tiles/cobertura fracionária, mapas completos por etapa, picos Python, comparação alternada, atalhos raster, cache de limites/paths e índice STR compacto/culling cilíndrico preservando PNG, clipping de cobertura dispensado com PNG idêntico, memória de processo em exports isolados, RGBA direto no Tk sem retenção inicial redundante e sete operações desktop comparadas em quatro casos/DPI com pixels/vistas idênticos | **Aceito localmente em 4.08–4.10**, com [base original, input humano, pixels, memória e limites](performance-acceptance.md). Bases arbitrariamente maiores, pausas densas, GPU e outras plataformas não têm garantia de fluidez |
| 5. Validação e distribuição | testes, wheel/sdist, dados/licenças, documentação, verificação offline e smokes desktop locais em Tk real, também no wheel sem Matplotlib/GIS | **Aceito:** 24/24 jobs reais para 0.2.0, core/gui instalados e arquivos/RECORD/licenças/docs verificados. Aceite visual Windows; Linux/macOS apenas CI, limitação de plataforma explícita |

Os cinco critérios estão fechados no escopo documentado e no escopo de plataforma documentado. Cada um exige código funcional, regressões úteis e exemplos
verificados. Alterar a string de versão só ocorrerá depois desse corte;
publicação no PyPI é uma operação separada, ainda não realizada.

Avanço desktop: Tk recebe RGBA direto, libera imagens anteriores e não retém
referências redundantes. A consolidação de [lifecycle](component-lifecycle.md)
corrige desconexão de callbacks/ticks descartados, visibilidade de texto interno
e registro da colorbar antes do redraw. Há regressões, exemplo antes/depois e
sete cenários Tk adicionais; ainda falta ampliar propriedades/integrações.

No experimento anterior de RGBA, o viewer não retém
Scene/cópia inicial redundantes. Sete operações foram comparadas em quatro
casos/DPI, em 16 workers novos seriais: pixels e vistas idênticos, redução local
de memória e tempos variando nos dois sentidos. O redesenho ainda leva segundos;
não se fecha desempenho. Veja [medidas e limites](viewer-performance.md).

Consolidação adicional de desempenho: PNG reutiliza o primeiro tile de
geometrias e libera temporários após uso; a comparação em 24 workers novos
preserva as imagens e mede uma redução local de pico de até 4,0% nos casos
testados. O tempo ficou praticamente estável, com pequenas variações nos dois
sentidos. O atlas a 200 DPI ainda chega a cerca de 401 MiB: buffers do
canvas/redimensionamento, mais cenários, GUI e CI permanecem necessários.
Veja [amostras e limites](performance.md#reutilização-e-liberação-de-buffers-png).

Etapa posterior entregue: composição e redução BOX em faixas para buffers
grandes, com imagens byte a byte iguais. Na comparação isolada de dois pares
por caso/DPI, pico mediano do atlas em 200 DPI caiu de 401,10 para 288,08 MiB
(28,2%); São Paulo/200 DPI, de 192,01 para 156,17 MiB (18,7%). O tempo teve
pequenas variações nos dois sentidos; não há aceleração geral declarada.
Canvas completo, cobertura/preparação, cenários densos, GUI e CI continuam
pendentes. Veja [dados e limites das faixas](performance.md#canvas-composição-e-redução-box-em-faixas).

Etapa de cobertura entregue: aritmética de áreas/recortes preserva os PNGs e
reduziu tempo mediano local entre 6,6% e 13,3% em cinco casos/DPI. Nove pares
adicionais de estilos/recortes/hachuras contra Agg ampliam o diagnóstico visual,
sem provar igualdade com todo o sistema Matplotlib. Integrações de composição,
ornamentos/viewers, bases densas, GUI e CI permanecem abertas. Veja
[qualidade](style-quality.md) e [medições](performance.md#aritmética-da-cobertura-dos-traços).

Integração de composição entregue: supxlabel/supylabel, título global e textos
da Figure posicionáveis/editáveis; reservas seguem tight/constrained e o modo
automático/manual. Doze regressões, 16 estados diretamente registrados de
Matplotlib e atlas comparados ampliam a validação. Há diferenças de métricas e
solver; textos livres/cax, mais casos densos, GUI e CI permanecem pendentes.
Veja [rótulos globais](figure-labels.md). Nenhum critério é declarado fechado.

Edição adicional entregue: MapText/Annotation com posição e destino independentes,
offset points físico, alinhamento/fontes e lotes prospectivos; título de legenda
e rótulo de colorbar preservam estado após estilo inválido. Treze regressões e
19 contratos registrados da referência ampliam o primeiro critério. Text/Transforms,
setas completas, demais propriedades e validação GUI/CI ainda exigem trabalho.
Veja [texto editável](text-edits.md); não se declara o critério fechado.

Validação desktop local entregue: nove cenários com widgets/event loop Tk
reais em janelas ocultas, inputs sintéticos e Save produzindo arquivos estáticos.
Eventos selecionados foram comparados diretamente com TkAgg; callbacks,
passos fracionários e cleanup têm regressões. CI configurada para três sistemas
× cinco versões Python e smokes Tk por sistema, mas execução remota ainda
pendente. O smoke em Tk funcional do quinto critério foi realizado localmente;
aparência/input nativo, outros sistemas e medições densas permanecem abertos.
Veja [validação desktop](viewer-validation.md). Nenhum critério é fechado.

Input Tk ampliado: teclado/modificadores/botões, transições Axes/Figure e
keymaps editáveis/ciclos de grades com referência direta. Onze regressões
e smoke de treze cenários validam integração funcional, sem declarar input
nativo em outras plataformas nem equivalência completa de classes de eventos.
Veja [contratos e limites](viewer-input.md).

## Ordem de implementação

Auditoria integrada de Artists entregue: normalização de números, validação
antecipada de fontes/tamanhos, tracejados imutáveis, lotes prevalidados de
Spine/outline/LegendFrame e criação/edição de escala/ticks. Há 12 regressões,
52 subtests, referência direta e sete verificações Tk adicionais. Três subpassos
do primeiro critério têm evidência encerrada; o critério inteiro segue parcial.
Veja [progresso por subpasso](release-progress.md) e [auditoria](artist-validation.md).

Novo lote de consolidação entregue: caixa vertical da fonte em todos os
componentes de texto, correção de títulos multilinha, labelpad físico,
marcadores D/d/estrela e espessura de +/x; notação científica/offsets editáveis
e prefixos SI em eixos/colorbars. Dezoito regressões, 96 estados tipográficos,
54 composições atualizadas e dez cenários Tk ampliam os critérios 1–3 e 5.
Persistem hinting/avanços horizontais/solver diferentes, recomposição científica
HTML, MathText/TeX, casos densos, aparência/input nativo e CI remota. Nenhum
critério é declarado fechado; versão permanece 0.1.0 alpha.
Veja [exemplos e limites](numeric-formatting.md).

### O que ainda falta para fechar o corte

São cinco blocos de aceitação, não as 16 frentes do inventário completo:

1. **Artists existentes:** terminar a auditoria do conjunto 2D anunciado,
   integrar edições em exportação/viewer e corrigir inconsistências encontradas.
   A API integral de Matplotlib/Transforms não é requisito deste corte.
2. **Composição:** conferir títulos, ticks e componentes juntos em mapas simples,
   atlas e tamanhos/DPI diferentes, respeitando posições manuais e os limites
   documentados dos solvers; corrigir problemas materiais de integração.
3. **Acabamento:** comparar PNG/SVG e a janela com a referência direta, corrigir
   diferenças materiais de traços/textos/recortes/ornamentos e registrar os
   limites. Não é uma promessa de igualdade de pixels entre motores distintos.
4. **Desempenho:** concluir medições desktop e ampliar casos detalhados/densos;
   reduzir os gargalos observados sem alterar a imagem ou descaracterizar a API.
   As medições locais não substituem pintura visível/input nativo ou outras máquinas.
5. **Validação/release:** obter resultados reais da CI Windows/Linux/macOS nas
   versões suportadas, conferir input/aparência nativa, auditar nome/licenças/
   instalação/documentação e então fechar changelog, versão e pacotes 0.2.0.

Urbano, 3D, Qt e formatos novos permanecem depois do corte. Publicar no PyPI
é uma operação separada. A contagem de blocos só cai quando um critério inteiro
passa; entregas dentro de cada bloco reduzem seu trabalho pendente.

1. Consolidar os lotes de campos/cores/linhas e a edição de contornos/rótulos entregue; revisar propriedades e limites restantes.
2. Hierarquias com spans/subgridspec/mosaicos, eixos compartilhados/label_outer e vínculo HTML cilíndrico com histórico global foram entregues. Escala/norte/rosa acompanham o pan/zoom cilíndrico; ampliar integrações de composição e navegação geral antes das expansões futuras.
3. Comparar mapas completos e medir composição/raster, corrigindo os gargalos.
4. Executar validação de desktop e CI; concluir documentação e auditar o pacote.
5. Fechar changelog, versão 0.2.0, builds e instalação limpa.

O objetivo é uma versão delimitada e verificável. Novos requisitos podem alterar
o escopo; sem medições e CI concluídas, estimar uma data seria especulação.

Lote ampliado de composição: setters públicos de dimensões/DPI, três títulos
independentes e primeiro draw Tk seguro; 54 casos próprios e 14 cenários Tk
ampliam a integração. Há nove falhas registradas da referência neste roteiro
aninhado específico, diferenças de solver e conferência nativa pendente.
Veja [contratos, galeria e limites](sizing-composition.md). Esse lote era uma
entrega parcial; o estado atual dos aceites é o da checklist.

Lote ampliado de séries/estilos entregue: grupos e matrizes em plot, data por
nome, ciclos próprios condicionais, folhas locais/stacks/contextos, defaults
e texto lazy de legenda estáveis. Há referência direta, 21 regressões e 12
cenários Tk adicionais. Gaps/máscaras/units, integrações densas e aparência
nativa/CI real permaneciam pendentes naquele lote. O corte 0.2.0 foi posteriormente
encerrado no critério documentado: visual Windows e CI nos três sistemas.
Veja [contratos e galeria](series-styles.md).
