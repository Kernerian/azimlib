# Fase D — composição cartográfica editorial

Continuação de Lucide 0ae3af1151a642c28dc66f0fc0189f2036959784 e da Fase C.
CPU,Figure/MapAxes/Layer existentes,sem publicação nem aceite visual presumido.

## Insets e locators

Axes.inset admite Body/contexto próprio opcional,projeção,viewport,facecolor,
moldura e bounds normalizados. O default herda contexto; dados/Artists não são
compartilhados mutavelmente. target.locator(source,sync=True,shade=False,
mask_outside=False,connectors=False,samples=256) desenha o footprint geográfico
obtido pela inversa da projeção do viewport de origem, não um retângulo de tela
transplantado. O limite convexo ortográfico usa bisseção radial48 passos;
amostragem32..2048+quinas. Recusas para sementes/domínios não demonstrados.
Polos estereográficos globais podem produzir duas paralelas de um anel; não
inventar um interior simples. Preenchimento de footprints globais/polares
ambíguos é recusado; fronteiras permanecem disponíveis. Recorte e antimeridiano
reutilizam o projetor. Máscara externa demonstrada em alvo cilíndrico regional.
Conectores são apresentação, não rota geográfica.

link_view(source,target,bidirectional=False) sincroniza limites angulares de
Axes vivos com mesmo contexto na mesma Figure. Ligações formam DAG; duas vias
são um par explícito protegido contra recursão, ciclos adicionais recusados.
remove desliga callbacks. Locator sync observa a origem ao redesenhar, sem
alterar seu viewport. Corpos diferentes exigem correspondência científica
externa: não há transformação entre Terra/Marte inferida.

## Legendas, fluxos e páginas

LegendSection(title,handles,labels=None),from_group e Axes.legend(sections=...)
produzem headings em negrito, colunas sem separar seção, handles vetoriais,
ícones/efeitos,hatches e gradientes amostrados. fontsize,symbol_size,gaps,
alinhamento,bbox e modo expand continuam no motor existente. FlowScale com
valores/unidade/larguras tipográficas autorais fornece width e keys para uma
legenda explícita; Axes.flow_path não inventa volume ou unidade de fluxo.

Figure.cartographic_page(...) retorna CartographicPage com Axes principal,
faixa de título/subtítulo,sidebar para legenda/notas e crédito. Orientação
auto/portrait/landscape, margens/gap em pontos físicos,sidebar fracionária;
reflow ao mudar dimensão. Figure/Axes/TextArtists continuam editáveis.
Páginas pequenas/notas excedentes são recusadas, não comprimidas até ilegíveis.
page.locator cria um inset real; page.legend usa a mesma Legend. O layout é um
modelo programático de página, não solver universal de atlas nem editor desktop.

## Labels

O motor existente já fornecia point,line(tangent block),curve(glyph/cluster),
prioridade,interior de áreas,offsets,halo,leaders,repetição,escala e overrides.
Agora aceita RegionDefinition/CartographicPath/PlanetaryData e fontes temáticas;
artist.labels_for(text,...) cria labels com ownership/contexto e visibilidade
associados. Grupos podem instanciar fontes e labels com referência rebinculada.
Obstáculos incluem símbolos temáticos,legendas/insets/textos; collision_exclude
aceita folhas do mesmo Axes. Budget4096candidatos global e por camada.
Não há ótimo global garantido. Textos simples em curvas não deformam caracteres;
scripts conectados/combining sem shaping são recusados, HarfBuzz usa clusters.
Math/TeX curvos são recusados: usar bloco tangente e preservar tipografia.

## Temas

CartographicTheme imutável, get_theme e Axes.set_theme(None|name|theme).
Presets atlas,historical,political,physical,scientific,geological,
planetary-exploration. Defaults visuais < tema < grupo próximo < folha local.
Nenhum tema adiciona dados/fronteiras ou converte ciência. Papéis base,símbolos,
regiões,paths,labels,legenda,inset,background,moldura/orientação/raster explicitados.
Apenas propriedades realmente integradas são aplicadas; tema não assume oceanos
em Marte. Remover tema restaura background original e preserva edições locais.

## Evidência

Tests test_editorial_050.py,test_groups_050.py e regressões de labels da0.4.
Galeria examples/thematic/editorial_050.py: atlas terrestre com base NaturalEarth
+ ficção explícita; exploração de Marte com raster sintético por padrão ou
Viking real existente explicitamente fornecido; Lua global/regional e polo/global.
PNG/SVG/PDF reais,mesma API. A aprovação humana dos novos mapas continua pendente.
Domínios regionais e recusas são parte do contrato; não suporte universal a
projeções interrompidas,domínios não convexos ou corpus geológico factual.
