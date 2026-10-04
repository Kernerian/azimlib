# Reutilização do viewport e descarte conservador

O desenho mantém os mesmos dados e Artists. Não simplifica coordenadas nem
muda fonte, estilo, DPI ou distância da escala.

## Limites reutilizáveis

Geometry e FeatureCollection, imutáveis, calculam seus limites uma vez, quando
solicitados. Edição de uma linha cria outra geometria/coleção e recebe outros
limites. A serialização GeoJSON, igualdade e campos públicos não mudam.

Viewport reutiliza a mesma amostragem dos limites projetados, com cache de
128 combinações projeção/extent. O tamanho/posição do canvas não entra na chave:
escala e offsets continuam sendo calculados para cada box. Parâmetros diferentes
de projeção e novas extensões têm entradas distintas; evicção recalcula o resultado.
Somente as seis classes internas exatas e imutáveis participam. Projeções
customizadas/subclasses continuam chamando forward a cada construção.

Este cache guarda quatro limites. Separadamente, o [cache de paths projetados](projected-paths.md)
reutiliza vértices de linhas/polígonos em armazenamento limitado; nenhum guarda cenas.

## Descarte por vista

`fig.to_scene(cull=True)` pode omitir linhas/polígonos inteiramente fora do
viewport em Mercator e equiretangular. O teste usa uma caixa projetada
conservadora, com folga para espessura, caps/junções e rasterização. Linhas
atravessando o mapa e polígonos que o contêm continuam sendo desenhados, mesmo
que nenhum vértice esteja dentro da vista. Buracos e hachuras permanecem iguais.

Não descartamos automaticamente geometrias com envelopes ambíguos no
antimeridiano, amplitude longitudinal de 180° ou mais, projeções diferentes,
curvas, arrowheads, marcadores ou símbolos. Scatter, campos, vetores e labels
continuam pelo caminho existente. GeometryCollection examina seus filhos.
As chamadas de feature_style e os índices originais de cores não são alterados.

Há agora um [índice espacial próprio](spatial-index.md) para coleções elegíveis
com pelo menos 64 features. Ele consulta caixas projetadas e mantém a varredura
nos casos de callback/estilo/projeção que exigem o caminho completo. Listas de
overrides ainda são examinadas para determinar a folga. Em bases densas com
muitas features visíveis, os gargalos podem continuar no raster.

## Exportação e navegação

savefig utiliza o descarte conservador; um override de DPI menor que o da
Figure conserva a cena completa para evitar diferenças na folga raster.
O desktop recompõe os dados na nova extensão e usa culling em cada desenho.
Histórico, escala, rosa/seta, insets e foco do minimapa seguem o estado dos Axes.

`to_scene()` mantém `cull=False` por padrão, e `to_html()` usa a cena completa.
O HTML portátil transforma uma cena exportada sem consultar novamente os dados;
omitir geometria nessa cena faria áreas desaparecerem durante o pan. O caminho
`to_svg()`/repr inline também continua completo; o SVG de savefig pode ter menos
paths invisíveis com a mesma área pintada.

## Validação e reprodução

As regressões comparam PNG completo/otimizado, cruzamentos, polígonos envolventes,
buracos/hachuras, overscan, antimeridiano, longitude não normalizada, subclasses,
parâmetros/resize, evicção, callbacks, cores por feature, edição, histórico,
insets e minimapa. A referência anterior do próprio viewport é mantida somente
no tool de desenvolvimento, fora do runtime/wheel.

```bash
python tools/compare_composition.py --repeats 4 --output composition.json
```

Os três modos são alternados: viewport anterior sem cache, cache com cena
completa e cache com descarte. Todos usam os limites imutáveis atuais e o mesmo
renderer. A medição inclui layout/composição; PNG é comparado depois das amostras.
O caso dense é uma malha de 2.501 polígonos sintéticos, sem validade territorial.
Não mede latência real da GUI nem memória nativa. Veja [resultados](performance.md).
