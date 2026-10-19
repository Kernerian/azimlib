# Azimlib 0.5.0 — Planetary Cartography / Beyond Earth

Estado: proposta normativa ampliada; Fase A implementada no recorte documentado.
[Contratos efetivos](foundation-0.5.md) e [evidências](foundation-validation-0.5.md)
distinguem entrega parcial da proposta completa, ainda não concluída.
Data de consolidação: 2026-10-18. As 19 frentes abaixo são cumulativas: as
dez frentes planetárias anteriores permanecem integrais. A identidade principal
continua Beyond Earth, com uma camada temática, histórica, educacional e
editorial compartilhada entre Terra e outros corpos.

Este planejamento vive em uma branch separada. Não altera a versão, os pacotes,
a tag, a Release nem a documentação publicada/congelada da 0.4.0.
[Checklist proposta](release-plan-0.5.md), [sequência de versões](future-versions.md),
[roadmap](roadmap.md). Nomes de APIs futuras e caminhos de exemplos são propostas,
não interfaces existentes ou assinaturas já estabilizadas.

## Contrato de arquitetura e escopo

- Uma única infraestrutura Figure/Axes/Artist: mesmos símbolos, áreas, paths,
  grupos, texto, legendas e insets em qualquer Body ativo. Não criar uma API
  exclusiva de mapas históricos nem outro sistema de plotting para planetas.
- Separar dado/geometria de estilo, apresentação e modelo científico. Uma
  suavização editorial não muda uma rota científica; um tema não cria dados.
- Identificar Body, datum, frame, época, unidades, orientação e convenções.
  Não transformar silenciosamente dados da Terra para Marte ou projetar um
  footprint entre corpos distintos sem uma relação explicitamente definida.
- Tamanhos físicos de impressão, pixels, unidades do mapa e distâncias da
  superfície são conceitos distintos. A legenda usa amostras visuais coerentes,
  sem deformar símbolos com o aspecto ou a rotação do viewport.
- Preservar CPU como padrão e os imports raiz/pyplot. Não exigir GPU, serviços
  online ou downloads implícitos para os exemplos básicos.
- Continuar como biblioteca programática de cartografia/plotting: não é um editor
  gráfico completo, GIS desktop, motor orbital ou ferramenta de navegação de missão.
- Nenhuma frente foi retirada. Domínios ainda não demonstrados, como operações
  gerais sobre malhas irregulares, exigem contrato próprio, evidência e estado
  explícito; não podem aparecer como concluídos por um fallback esférico oculto.

## Frentes consolidadas

### 1. Modelo público de corpo celeste

Identidade/nome, tamanho/forma, esfera, elipsoide e modelo triaxial, meridiano
principal, eixos, orientação e convenções. Terra vira preset preservando seus
defaults. Lua, Marte, Vênus e Mercúrio são os candidatos iniciais; extensão para
outras luas, planetas anões, asteroides e malhas irregulares fornecidas
explicitamente. Constantes devem ter fonte/versionamento e domínio declarados.
O Body interno da 0.4.0 é somente uma fundação oblata, não esse contrato público.

### 2. Coordenadas e referenciais planetários

Coordenadas planetocêntricas/planetográficas, direção e intervalo de longitude,
unidades, datum, época e frame/orientação explícitos. Validar polos, alturas,
superfícies e transformações permitidas. Não confundir datum com Body ou
introduzir mudanças de referencial sem dados. Preservar o modelo de tempo e as
recusas explícitas existentes; modelos novos exigem fontes e validade próprias.

### 3. Projeções e geodésia por corpo

Projeções globais, regionais, polares e mapas globais planificados; distâncias,
azimutes, rotas, comprimentos, áreas, unidades físicas e perfis de elevação entre
pontos. Validar inversas, antimeridiano e singularidades por modelo. Geodésia
triaxial/irregular não herda automaticamente fórmulas terrestres: pode exigir
pesquisa numérica. A planificação de malhas irregulares permanece uma subfrente
de pesquisa separada, sem promessa de solução universal nesta release.

### 4. Raster, imagens e relevo extraterrestre

DEMs, imagens orbitais georreferenciadas, mosaicos, texturas, relevo 2D/3D,
hillshade e exagero vertical explícito. Declarar datum vertical, resolução,
NoData, interpolação e unidades; recusar mistura incompatível de superfícies.
Navegar de corpo inteiro a região, feição e terreno local sem perder a referência.

### 5. Feições e cartografia geológica

Crateras, vulcões, montanhas, cânions, mares lunares, calotas, falhas e regiões
nomeadas; unidades e legendas geológicas. Separar geometria/classificação de
símbolos e nomenclatura; preservar fonte, língua, época e incerteza. Reusar as
primitivas genéricas das frentes 11, 12, 15 e 16.

### 6. Iluminação planetária

Estender iluminação, terminador e incidência da 0.4.0 com Body e orientação
corretos. Modelos atmosféricos somente com dados, física e limites declarados.
Tratar tempo/frame, normais da superfície, horizonte e escalas visuais
explicitamente. Não promover eclipses a previsão científica certificada.

### 7. Exploração e evolução temporal

Locais de pouso, trilhas/waypoints de rovers, áreas exploradas e rotas científicas;
calotas sazonais, poeira e iluminação temporal quando houver dados apropriados.
Separar data da observação, validade e animação; uma interpolação visual não
constitui previsão. Compartilhar Artists, picking, tempo e exportação existentes.

### 8. Comparação entre mundos

Múltiplos corpos na mesma Figure, escalas físicas ou normalização visual
identificadas. Corpo inteiro → região → feição → terreno local; comparar polo
com globo e dois mundos sem sugerir que possuem a mesma escala quando não têm.
Combinar subfiguras, insets e composição editorial existentes/estendidos.

### 9. Integração com a API existente

Scatter, linhas, raster, terreno, labels, escalas e GeoJSON operam no Body ativo.
GeoJSON externo precisa de contexto explícito quando suas coordenadas não forem
terrestres; não reinterpretar seu contrato terrestre silenciosamente. Manter
lifecycle, callbacks, picking, stale/invalidação e exportação; oferecer migração
para mudanças públicas necessárias e compatibilidade dos defaults da Terra.

### 10. Dados, precisão e proveniência

Constantes autoritativas, datum/época/frame, unidades e licenças por dataset,
fonte, ícone, imagem e modelo. Validadores independentes com tolerâncias e
domínios definidos antes da avaliação. Registrar resultados, falhas e limites;
não anunciar precisão universal. Incluir dados sintéticos reproduzíveis e
aquisição externa opcional, explícita, verificável por hash e limitada por recursos.

### 11. Símbolos e ícones cartográficos georreferenciados

Sistema genérico de símbolos nativos, marcadores vetoriais, SVG customizado,
PNG/imagens externas e símbolos do usuário; categorias, tamanho visual ou em
unidades do mapa quando aplicável, rotação, opacidade, zorder, âncora, offsets,
clipping, prioridade visual, labels associados e legendas automáticas/explícitas.

Usos: ouro, sal, marfim, portos, cidades, fortalezas, batalhas, minas, templos e
recursos; pousos, sondas, rovers, bases, instrumentos, pontos científicos e
feições especiais. O catálogo não deve inferir dados nem direitos sobre assets
externos. SVG importado terá subconjunto documentado e validação de recursos,
sem scripts, entidades externas ou carregamento remoto implícito; elementos
não suportados devem falhar explicitamente ou ter fallback declarado.

### 12. Regiões e áreas temáticas personalizadas

Polígonos/multipolígonos e uma ou várias geometrias independentes de limites
administrativos: impérios, reinos, territórios, zonas culturais/linguísticas,
áreas econômicas, biomas, exploração, unidades geológicas e regiões científicas.
Preenchimento, alpha, contorno, hatches/padrões, máscaras, sobreposição, prioridade,
label central/calculado, clipping geográfico, antimeridiano e diversas projeções.

Oferecer escolha explícita entre área binária, polígonos discretos, bandas/degraus
de intensidade e gradiente matematicamente apropriado. Núcleo, controle,
influência, fronteira aproximada e alcance provável são semânticas fornecidas
pelo autor: a biblioteca não as infere nem transforma mapas históricos em heatmaps.
Gradiente decorativo e campo quantitativo/incerteza precisam de legendas distintas.

### 13. Rotas, fluxos e curvas cartográficas

Polilinhas, waypoints, curvas suaves, Bézier, splines, arcos geodésicos e paths
explícitos. Setas opcionais, direção, espessura, cor, alpha, tracejado, símbolos
ao longo da linha, labels na rota, clipping e efeitos que preservem a geometria
científica original. Declarar o espaço em que a curva é construída: geográfico,
superficial ou visual/projetado; não interpolar longitude através da emenda errada.

Comércio, migração, expedições, campanhas, ferrovias esquemáticas, rotas marítimas,
fluxos econômicos e conexões urbanas; rovers, travessias e caminhos entre pousos
e regiões de interesse usam a mesma infraestrutura. Separar quatro contratos:
**editorial**, **geodésico**, **calculado em rede/grafo** e **trajetória física**.
O último continua pertencendo ao planejamento orbital 0.6.0; não é inferido de
uma linha curva desenhada no mapa. Largura proporcional exige unidade e legenda.

### 14. Inset maps, minimapas e locator maps

Estender os MapAxes/insets existentes para um ou vários mapas secundários:
posição, tamanho, frame, background, projeção e viewport próprios, Body próprio
quando aplicável, retângulo/polígono localizador, foco destacado, conexões
opcionais, máscara fora do foco e sincronização opcional com o mapa principal.

Projetar o footprint geográfico real entre projeções, evitando um simples
retângulo de tela quando ele for incorreto. Tratar horizonte, polos,
antimeridiano e ciclos de sincronização. Insets de corpos distintos permitem
comparação, mas não um locator geográfico automático sem correspondência física.
Casos: Marte → Jezero, Lua → Apollo, polo → mapa global, corpo → terreno local,
mapa-múndi → região e detalhe local dentro de mapa regional.

### 15. Composição cartográfica editorial

Legendas heterogêneas com linhas, áreas, ícones/símbolos, grupos e seções; títulos,
subtítulos, caixas explicativas, notas, fontes/proveniência, escala gráfica,
rosa dos ventos, indicadores de orientação, molduras e neatlines. Layout entre
mapa principal, legenda e insets; decoração opcional separada da geometria.
Montar uma página de atlas/didática sem edição gráfica para tarefas básicas e
preservar exportação SVG/PDF para edição externa. Não substituir a rosa pela
seta norte nem vice-versa. Em outro Body, declarar o significado do norte,
inclusive convenções rotacionais, e evitar escala única enganosa em projeção variável.

### 16. Labels e anotações cartográficas avançadas

Pontos, áreas, linhas e texto seguindo curvas; rotação, halo, outline, background,
callouts/leader lines, offsets automáticos, prioridade, colisões, exclusão
seletiva de colisão, regras por escala e repetição/ocorrência única. Permitir
nomes grandes de impérios, oceanos, desertos ou regiões atravessando uma área
por baseline explícita ou calculada, sem inventar topologia textual no dado.
Preservar internacionalização/shaping e clusters; não prometer curvar um bloco
TeX arbitrário quando o pipeline só aceita um bloco rígido. Declarar limitações.
Resolver candidatos de modo determinístico, com orçamento de recursos e
prioridade diferenciada para labels, símbolos, legenda e insets.

### 17. Camadas temáticas e grupos

Organizar base física, fronteiras, território, comércio, recursos, cidades,
labels e anotações por extensão compatível de Artists/Layer. Visibilidade,
zorder, clipping, estilos compartilhados, inclusão/exclusão na legenda e
reutilização entre layouts/insets, com interação e invalidação corretas.
Compartilhar dados/definições não significa anexar o mesmo Artist mutável a
dois Axes: usar instâncias por viewport ou mecanismo equivalente com ownership
explícito. Proibir ciclos de grupo e herança de estilo ambígua.

### 18. Estilos temáticos reutilizáveis

Temas configuráveis/extensíveis para fronteiras, água, terreno, labels, cidades,
rotas, símbolos, legenda e inset. Presets opcionais atlas, histórico, político,
físico, científico, geológico e exploração planetária. A API granular permanece;
documentar precedência entre defaults, contexto, grupo e edição individual.
Temas não contêm territórios, datas, classificações ou outros dados disfarçados
de estilo; não supor oceanos/continentes terrestres em todo Body.

### 19. Exportação editorial e composição multiplataforma

Novas primitivas em PNG, SVG e PDF onde o backend correspondente suportar;
DPI, dimensões e páginas consistentes em Windows/Linux/macOS. Preservar vetores
SVG quando possível para texto, rotas, polígonos, símbolos, molduras e insets;
paths de glyphs são vetoriais, mas não equivalem a texto editável/semântico.
Declarar quando shaping, fonte ou backend exigirem outlines, embedding ou raster.
Não converter silenciosamente uma página inteira para bitmap por causa de um
ícone. Testar clipping, alpha, blending, fontes, padrões, imagens, efeitos e
fallbacks. Consistência visual/física não significa igualdade pixel a pixel
entre todos os sistemas e renderizadores.

## Reuso real da 0.4.0 e infraestrutura nova

Os caminhos abaixo referem-se ao código existente no SHA da tag v0.4.0. Reuso
significa base disponível, não cobertura já demonstrada dos novos requisitos.

| Base existente | Reuso | Extensão necessária |
|---|---|---|
| `_frames.py`: Body/ReferenceFrame internos; `geodesy.py`, `crs.py` | Frames/unidades e geodésia delimitados | Body público, triaxial/irregular, orientação e coord. planetárias (1–3) |
| `artist.py`, `layers.py`, `collections.py`, `transforms.py` | Lifecycle, visibilidade, estilo, picking/transformações | Grupos sem ownership duplicado e instâncias por viewport (9/17) |
| `path.py`, `projected_paths.py`, `axes.py`: route | Paths, segmentação, geodésia/rotas atuais | Espaços de curvas explícitos, efeitos e símbolos de rota (13) |
| `axes.py`: inset/inset_axes/overview; `nested_layout.py` | Mapas filhos e overview existentes | Locators por footprint, Body distinto, sincronização controlada (14) |
| `label_layout.py`, `polygon_labels.py`, `line_labels.py`, `curved_text.py`, `text_engine.py` | Candidatos, colisões, texto curvo e shaping delimitado | Labels extensos de área, regras de escala/grupo e obstáculos integrados (16) |
| `components.py`, `legend_handler.py`, `legend_layout.py`, `layout_engine.py` | Legendas, escala, orientação e composição | Seções heterogêneas e layout editorial integrado (15) |
| `styles.py`, `style.py`, raster/terrain/volume e renderers | Estilos, exportações e relevo existentes | Temas sem dados, símbolos importados e matriz de capacidades (4/11/18/19) |
| `solar.py`, `lunar.py`, `lighting.py`, `temporal.py` | Modelos terrestres/temporais limitados | Iluminação Body-aware com dados/validade próprios (6/7) |
| `overlay.py`, leitores, máscaras e hatches existentes | Geometrias e preenchimentos | Regiões editoriais graduais e clip comum por Body (12) |

Infraestrutura nova compartilhada: contexto de Body por Axes/Artist/dataset,
registro seguro de símbolos/assets, geometria vs aparência dos paths, grupos
e instâncias, sincronização de viewport, composição editorial e declarações
de capacidades por backend. Nenhum desses contratos é atendido apenas por
renomear um objeto interno ou adicionar um novo preset.

## Dependências e fases sugeridas

10 (dados/proveniência) e 9 (contratos/API) acompanham todas as fases. A ordem
abaixo é de implementação sugerida; não substitui os 19 IDs de frente.

| Fase | Frentes principais | Dependências e saída verificável |
|---|---|---|
| A — contratos/fundação | 1, 2, 9, 10; desenho de 17 | Body, ownership, unidades, domínios e matriz de capacidades; regressão Terra |
| B — superfícies | 3, 4, 6 | A; projeções/geodésia/raster/luz por corpo; fixtures independentes |
| C — primitivas temáticas | 11, 12, 13, 17 | A + operações de B; símbolos, áreas, curvas e grupos com paridade Terra/Marte |
| D — página cartográfica | 14, 15, 16, 18 | C; labels e insets integrados a layout/legendas; temas opcionais |
| E — aplicações Beyond Earth | 5, 7, 8 | B/C/D; geologia, exploração e comparação Lua/Marte/Vênus/Mercúrio |
| F — validação e entrega | 19 + fechamento de 9/10 | Todas; exemplos, migração, CI, aceite humano e evidência de distribuição |

Dependências diretas: 2 ← 1; 3 ← 1/2/10; 4 ← 1/2/3/10;
6 ← 1/2/4/10; 11 ← 9/10/17; 12 ← 2/3/9/10/17;
13 ← 2/3/9/10/17; 14 ← 1/2/3/9; 16 ← 11/12/13/14/17;
15 ← 11/12/13/14/16/17; 18 ← 11–17; 5 ← 4/10/11/12/16;
7 ← 6/10/11/12/13/17; 8 ← 1/3/4/14/15; 19 valida o conjunto.
17 fornece o contrato de grupos antes das primitivas; integração final de
colisões/layout ocorre em D. Evitar dependência circular entre legenda e labels.

## Casos futuros de aceitação

| Caso | Conteúdo e evidência esperada |
|---|---|
| `examples/thematic/historical_trade_map.py` | Mapa regional terrestre, áreas territoriais, cidades, recursos, rotas curvas, labels, legenda mista, orientação e locator mundial; dados próprios/públicos/sintéticos documentados |
| `examples/planetary/mars_exploration_map.py` | Unidades geológicas, rota de rover, waypoints e minimapa global; mesmas primitivas de símbolos/áreas/rotas/grupos/legenda do caso terrestre |
| Lua: mares/crateras/Apollo | Locais de pouso, regiões e inset da Lua inteira; versão polar e detalhe local |
| Vênus: regiões e mosaico | Raster, regiões nomeadas e símbolos; georreferência e fontes explícitas |
| Mercúrio e comparação de mundos | Preset e referência validados; Figure comparativa com escalas físicas e normalizadas identificadas |

O primeiro caso reproduz uma estrutura didática de atlas, não o conteúdo ou
os assets de um mapa protegido do Império do Mali. Sem licença apropriada,
não copiar seus ícones, textos, geometria editorial ou ilustrações. Dados
sintéticos históricos devem ser identificados como esquemáticos, sem sugerir
que são uma reconstrução factual. Caminhos acima ainda não serão criados.

Cada caso deve mostrar edição de estilo, toggle de grupo, mudança de projeção,
exportação e pelo menos um teste de lifecycle/viewport. Aceite futuro inclui
imagens reais nos três sistemas, não apenas comparação de strings ou existência
de PNG. Nenhum aceite humano será inferido automaticamente.

## Riscos e critérios de validação

| Risco | Tratamento planejado |
|---|---|
| Geodésia triaxial/irregular, orientação e datum vertical | Pesquisa/modelos numéricos; domínios/tolerâncias antes dos testes; referências independentes; recusa onde não suportado |
| Emendas, horizonte, projeção e topologia de regiões/locators | Fixtures polos/antimeridiano/oclusão/multipolígonos; invariantes de geometria; sem retângulo aproximado oculto |
| Colisões de labels e layout combinatório | Heurísticas determinísticas, prioridades e override manual; sem promessa de ótimo global |
| Curvas editoriais confundidas com medidas físicas | Geometria original preservada; espaço da curva/unidade/modo explícitos em API e legenda |
| Incerteza territorial confundida com probabilidade | Autor define semântica; bandas/gradientes não inferem controle ou confiança estatística |
| SVG/imagens, fontes e direitos de terceiros | Subconjunto seguro, limites de recursos, hashes, licenças, embedding permitido; nada remoto implícito |
| Grupos/insets e caches compartilhados | Ownership e invalidação testados; evitar ciclos, vazamento de estado e cópias completas desnecessárias |
| Portabilidade/fidelidade/performance | Workloads fixos, memória/tempo medidos, capabilities/fallback explícitos; sem herdar budgets GPU não demonstrados |
| Crescimento de escopo | Lotes por contrato e exemplos verticais Terra/Marte desde C; nenhuma frente excluída ou adiada silenciosamente |

Há engenharia comum nas primitivas, lifecycle, importação limitada de assets e
integração de exportação; triaxial/irregular, orientação/iluminação científica e
validação de referenciais podem exigir pesquisa. Definir antecipadamente o
recorte demonstrável sem chamar o restante de concluído. Não fixar prazo de
release antes dessa análise por subdomínio.

## Limites entre versões e gates preservados

- 0.4.1: manutenção e refinamentos compatíveis; ensaio planetário somente com
  infraestrutura adequada, sem download planetário nesta máquina.
- Gates 0.4.0 **2.08, 9.08, 13.06, 13.07** permanecem formalmente adiados:
  IDs, critérios, budgets, tolerâncias, evidências e falhas preservados no
  [registro original](deferred-gates-0.4.md). Não promovidos nem renumerados.
- Melhorias de renderer/ciência podem apoiar 0.5 sem exigir fechamento desses
  gates como pré-condição automática. Certificação global de eclipses não é
  requisito obrigatório da 0.5.0; GPU não ganha garantia universal de latência.
- 0.6.0 continua **Orbits**: mecânica orbital, referenciais espaciais,
  trajetórias físicas e cenas do sistema solar. Não antecipar propagador ou
  planejamento de missão sob o nome de rota editorial.
- A checklist seguinte é proposta de implementação/validação futura, sem
  execução e sem autorização de publicação. Alterações de escopo exigem
  registro explícito; uma documentação de planejamento não conclui recursos.
