# Aceite de Artists 2D: checklist 1.10–1.12

O passo 1 é aceito no [catálogo do corte](artist-scope-0.2.md), após a
integração/auditoria descritas aqui. Isso não encerra layout, fidelidade visual,
desempenho ou validação multiplataforma dos outros quatro passos da 0.2.0.
A versão continua 0.1.0 alpha; não houve publicação.

Os hashes dos relatórios desse lote continuam históricos, resolvidos contra
snapshots exatos em `tools/baselines`, incluindo `interactive-tiles-before`.
Não são substituídos pelos hashes atuais sem executar novamente o roteiro.
[Validação atual](validation.md) e [galeria](release-gallery.md) registram a
nova suíte/exports, sem reabrir este catálogo por mudanças internas no viewer.

## 1.10 — Mapa integrado

O [cenário reproduzível](../tools/artist_acceptance_case.py) combina estados
reais da base Natural Earth embarcada com valores, estações, rota, imagem,
mesh, vetores e contornos **sintéticos**. Seis mappables compartilham a mesma
Normalize: geometria temática, scatter, mesh, imagem, quiver e contour.
Os dados geográficos permanecem imutáveis; cada handle edita seu próprio estado.

Verificações em colorbars horizontal/vertical e 100/200 DPI:

- Uma mudança de limites da norma é observada pelos seis mappables e pela
  colorbar; os rótulos de contornos acompanham a paleta.
- Edições de dados/estilos mantêm paths de contorno e os limites manuais
  definidos **antes** de criar as camadas.
- Ocultar/restaurar as seis camadas restaura a cena e os pixels editados nos
  casos Tk. Componentes cartográficos continuam opt-in e independentes.
- Remover camadas, rótulos e colorbar interrompe invalidações da antiga figura
  por alterações posteriores na norma compartilhada.
- PNG estático, RGBA direto e buffer Tk coincidem nos casos medidos; SVG é
  estático, sem UI. Pan/foco/Home conserva as edições existentes.

A inspeção da primeira imagem revelou que imshow sobrepunha o enquadramento
manual do mapa com seu próprio extent. A correção respeita os limites de cada
eixo bloqueado pelo usuário. Três casos de limites manuais (x, y ou ambos)
foram registrados diretamente com Matplotlib/Agg e comparados no teste.
**Diferença preservada:** nos eixos automáticos, a Azimlib continua aplicando
seu enquadramento exato/fixo ao criar uma imagem, em vez de reproduzir toda a
política sticky-edges/flags de autoscale do Matplotlib. Use limites explícitos
ou `ax.autoscale()` para escolher a política da vista; essa diferença não fica
escondida no aceite.

[Exemplo](../examples/artist_acceptance.py),
[antes](../gallery/artist-acceptance-before.png) e
[depois](../gallery/artist-acceptance-after.png), também em SVG/HTML.
O HTML é uma exportação: edições posteriores em Python exigem reexportação.

## 1.11 — Auditoria de propriedades e aliases

Os testes percorrem **28 handles/famílias de uso** do catálogo, incluindo
Figure/eixos, todas as camadas, textos internos de ticks/legenda/colorbar,
spines/frame/outline, escala, norte, rosa, overview e inset. Uma propriedade
desconhecida, junto de uma mudança de visibilidade, é rejeitada sem alterar
controles, cena SVG, callbacks ou estado stale nesses casos.

Correções acrescentadas:

- Alinhamentos ha/va inválidos são rejeitados no normalizador de estilo,
  incluindo aliases, antes de editar labels ou substituir ticks/locators.
- Textos não aceitam propriedades exclusivas de pontos/áreas: marker, ms e
  demais estilos de marcador, symbol ou hachuras. O erro não deixa posição de
  texto de Figure alterada nem ticks substituídos.
- Spine/outline e LegendFrame reconhecem os aliases aplicáveis (lw/ec/fc),
  rejeitando pares ambíguos antes de editar controles/estilo.
- `getp(handle, 'lw')` e os aliases existentes consultam a propriedade
  canônica; getters próprios têm prioridade. `getp(north, 'size')` consulta o
  tamanho da seta, sem reinterpretá-lo como fonte.
- Choropleth prepara norma/cmap/array enquanto está desconectado. Norma
  inválida ou conflito norm/vmin/vmax não deixa camada parcial anexada, vista
  alterada ou norma compartilhada parcialmente preenchida.

[Referência direta](artist-acceptance-reference.json) produzida pelo
[tool de desenvolvimento](../tools/inspect_artist_acceptance.py): estados
selecionados de aliases em linha/spine/frame, cinco rejeições e três vistas
de imagem. Os testes lêem o registro, sem importar Matplotlib.
As cores retornadas continuam com representações próprias, não tuplas RGBA
idênticas em toda consulta; o teste verifica a coerência de cada alias/getter.

## 1.12 — Aceite e limites

Aceite requer a suíte cumulativa sem falhas, regressões do conjunto acima,
execução em source/wheel, exports e relatório Tk com a mesma implementação.
O [smoke](../tools/smoke_artist_acceptance_tk.py) possui **14 verificações**
em janela Tk real **oculta**: duas combinações de DPI/orientação, edições em
ion agrupadas em um draw, roundtrip de visibilidade, rejeição sem redraw,
foco/Home, descarte e liberação do cache.

Relatórios [source](artist-acceptance-tk-source.json) e
[wheel instalado](artist-acceptance-tk-wheel.json) incluem hashes dos módulos
efetivamente importados, dos tools e o caminho do runtime. O core/wheel não
usa Matplotlib, Cartopy, GeoPandas, Shapely ou pyproj. CI inclui este décimo
smoke, mas **não foi executada remotamente** neste lote.

Limites que permanecem explícitos, sem impedir este aceite restrito:

- Não existe transação com rollback de vários Artists/callbacks customizados.
  `setp` em uma sequência e setters genéricos de Figure/MapAxes podem executar
  propriedades válidas em ordem; falha posterior não desfaz valores anteriores.
  Prevalidação de nomes evita propriedades desconhecidas no lote, mas não
  equivale à validação antecipada de todos os valores/setters arbitrários.
- Estilos de Layer usam vocabulário compartilhado: propriedades conhecidas
  destinadas a outra geometria podem ser armazenadas sem efeito no desenho.
  Textos rejeitam os estilos incompatíveis auditados; isso não é uma tipagem
  completa de todas as subclasses Artist do Matplotlib.
- Parsing de cores/fontes, listas de famílias, máscaras/gaps, contourf,
  Transform completo, MathText/TeX e formatos adicionais não fazem parte do
  catálogo deste corte. Callbacks de styling por feature são executados na
  composição e podem falhar nessa fase; não há avaliação antecipada universal.
- Permanecem as diferenças de contornos/precisão em
  [1.09](contour-boundaries.md) e a política automática de imagem acima.
- Janela oculta não comprova aparência, input físico, tempo de pintura ou
  suporte efetivo a outras plataformas. Esses checks continuam abertos nos
  passos posteriores. As geometrias reais aqui são generalizadas e não substituem a
  base original mais detalhada prevista em 4.08.

Evidências de regressão: [test_artist_acceptance.py](../tests/test_artist_acceptance.py),
além dos testes já ligados no catálogo. Próximo trabalho do roteiro: **2.08**.
