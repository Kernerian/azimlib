# Índice espacial próprio

Azimlib usa uma hierarquia de caixas delimitadoras STR implementada com stdlib.
Não utiliza Shapely, rtree, GeoPandas ou outro motor geoespacial.

A preparação ordena caixas em faixas e grupos espaciais, depois agrupa os nós
até a raiz. As folhas usam armazenamento imutável compacto de quatro float64
por caixa, sem quantização. Chaves inteiras originais e precisão de consulta
são preservadas. Essa construção substitui a ordenação em cada divisão binária
do primeiro BVH; não altera a API de `BoundsIndex`.

## Como participa do mapa

Com cull=True, camadas de geometria com pelo menos 64 features podem preparar
um índice de envelopes em metros projetados, em Mercator/equiretangular.
O índice é construído quando necessário, a partir dos mesmos limites usados
no descarte conservador. A coleção imutável reutiliza até quatro índices de
projeção, com evicção LRU. A estrutura guarda caixas/índices, não paths projetados.

A consulta percorre os ramos cujas caixas tocam o viewport, incluindo a folga
de linha/hachura e rasterização. Cada candidato ainda passa pelo teste existente
antes de desenhar. Os índices retornam em ordem original: cores por região,
feature_styles, transparência, z-order e sequência de pintura permanecem iguais.
Polígonos que envolvem a vista e linhas que a atravessam são incluídos mesmo
com todos os seus vértices fora da área visível.

Envelopes ambíguos no antimeridiano, amplitudes de 180° ou mais, geometrias
pontuais/compostas e limites fora do domínio finito são conservados no caminho
existente. GeometryCollection continua examinando seus filhos. Projeções
customizadas e outras projeções mantêm a varredura anterior.

Camadas com callback feature_style mantêm todas as chamadas, na ordem original,
e não usam o índice. Camadas cujo estilo base contém curvas, arrows, marcadores
ou símbolos também conservam a varredura. Overrides desses elementos por feature
entram na lista de candidatos obrigatórios. Overrides de estilo são lidos de novo
em cada composição: sua lista ainda tem custo linear, porém não reprojeta todas
as geometrias nem converte as cores de features descartadas.

## Edição e navegação

Editar uma linha com set_data ou substituir layer.data cria/reutiliza a coleção
correspondente; o índice de uma coleção antiga não é aplicado aos novos dados.
Alterar estilos, fonte da escala, DPI ou viewport recalcula a folga da consulta.
Modificar os parâmetros de projeção usa outro índice. Dados e JSON não mudam.

savefig e recomposição desktop usam o caminho otimizado. to_scene() padrão,
to_svg()/repr inline e to_html() continuam com a cena completa. O HTML portátil
precisa conservar geometrias para seu pan, sem recomposição de dados no browser.
Veja [contrato do viewport](viewport-performance.md).

## Uso direto de BoundsIndex

```python
from azimlib.spatial import BoundsIndex

index = BoundsIndex([
    (0, (-54, -26, -43, -19)),
    (1, (-74, -10, -60, 5)),
])
indices = index.query((-52, -25, -45, -20))  # (0,)
```

Cada entrada é um par (chave inteira distinta, bounds). Bounds são
(west, south, east, north) finitos, com mínimos menores ou iguais aos máximos.
Entradas/consultas precisam usar o mesmo espaço de coordenadas. O índice direto
não conhece CRS, antimeridiano, estilo ou projeção; essa preparação pertence ao mapa.
Retângulos que tocam a borda e caixas sem área são incluídos. query retorna
candidatos por envelope, não interseções topológicas. A árvore e suas entradas
são imutáveis; size informa a quantidade, bounds informa a caixa total ou None.

## Validação e limites

Consultas aleatórias são confrontadas com uma varredura independente, incluindo
toques, caixas duplicadas, polígonos envolventes e entrada editada depois da
construção. A composição indexada é comparada à varredura conservadora tanto
nas primitivas/metadados quanto nos PNGs. Há regressões de callbacks, índices
de cores, hachuras grossas, edição direta de estilos/dados, cache/evicção,
pan/zoom/DPI, antimeridiano, insets, minimapa e HTML.

```bash
python tools/benchmark_spatial.py --repeats 6 --memory --output spatial.json
```

A preparação inicial tem custo de tempo e memória. O benchmark distingue esse
custo das composições com índice reutilizado, alterna os modos e compara PNG
fora do cronômetro. A medição separada de memória usa uma coleção nova compartilhando
geometrias/bounds existentes: não representa o total da biblioteca, RSS ou buffers
nativos. As bases de 2.501/20.000 polígonos são sintéticas. Muitos envelopes
sobrepostos ou quase todas as features visíveis podem exigir percorrer a árvore
inteira. Não foi validada navegação de municípios detalhados ou latência real de GUI.

Para comparar a preparação/consulta anterior com o armazenamento compacto:

```bash
python tools/compare_spatial_builders.py --repeats 6 --output builders.json
```

Esse tool aquece os bounds igualmente, prepara índices novos em pares alternados
e mede alocações separadamente. Verifica chaves, Scene e PNG. Consulte os
[resultados e limites](performance.md) e o
[relatório bruto](performance/spatial-builders.json).
