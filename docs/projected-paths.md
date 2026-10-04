# Cache de geometrias projetadas

Linhas e polígonos imutáveis podem reutilizar suas coordenadas em metros
projetados ao navegar, redimensionar ou exportar novamente. Essa preparação
preserva a amostragem existente, cortes no antimeridiano, clipping polar Mercator
e horizonte ortográfico. Não simplifica, quantiza ou muda os dados originais.

## O que fica armazenado

O cache guarda paths multipartes, buracos e segmentos em bytes float64
imutáveis. A chave usa identidade da Geometry e parâmetros da projeção,
evitando recalcular um hash de todos os vértices. Geometrias distintas, inclusive
substituições por `set_data`, têm entradas distintas. Uma projeção interna
equivalente pode reutilizar a entrada da mesma geometria.

Somente as classes exatas `Geometry` e as seis projeções internas imutáveis
participam. Subclasses/projeções customizadas seguem o caminho anterior para
respeitar transformações dependentes de estado externo. `GeometryCollection`
examina seus filhos; Point/MultiPoint, scatter, labels, meshes, vetores e grid
não usam este cache de paths nesta etapa.

## Navegação e edição

Cada composição converte os metros projetados para a posição/escala atuais do
viewport e cria paths de tela novos. Pan, zoom, DPI e tamanho do canvas não
entram na chave. Estilos, cores por valor/feature, callbacks, hachuras, curvas,
marcadores e arrowheads continuam sendo calculados em cada desenho. Não se
guarda Scene, estilo, visibilidade, ornamentos ou resultado de layout.

Dados GeoJSON e seus campos públicos permanecem iguais. Modificar um path da
Scene não modifica o buffer do cache. Erros de preparação não são armazenados.
savefig, desktop, SVG e HTML usam a mesma preparação: o HTML continua recebendo
as geometrias completas para seu pan, sem recomposição de dados no navegador.

## Limites de memória

Há um LRU interno compartilhado, limitado a **16 MiB de payload** e **1.024
entradas**. O contador inclui bytes e tabelas de tuplas dos paths. Metadados,
objetos de projeção, memória temporária de preparação, buffers de tela, renderer
e RSS não estão incluídos: 16 MiB não é um limite da memória total do aplicativo.

Cada entrada referencia a geometria de origem por weakref; quando a origem é
liberada, seus buffers saem do cache. O índice não mantém coleções de dados
vivas. Uma geometria cuja preparação ultrapasse o orçamento é desenhada sem
retenção. Mudanças de projeção ou muitas geometrias podem provocar evicção:
a próxima vista recalcula o mesmo resultado. A primeira composição ainda paga
a preparação e a cópia para armazenamento; pode ser mais lenta que a anterior.

## Validação e medição

As regressões confrontam Scene/SVG/PNG com o caminho sem cache, incluindo seis
projeções, multipartes/buracos/vazios, antimeridiano, latitude polar, horizonte,
dados/estilos editados, callbacks, canvas/DPI, insets/minimapa e HTML.
Também verificam ausência de reprojeção no desenho aquecido, precisão após
mudança de viewport, LRU/orçamento, liberação da origem e projeções customizadas.

```bash
python tools/compare_projected_paths.py --repeats 6 --output paths.json
```

O tool alterna o compositor de geometria anterior da própria Azimlib e o atual,
mantendo o restante do viewport/índice/renderer igual. Separa primeira composição
sem cache de vértices, composição aquecida, zoom, alocações Python e PNG. Os dados
e bounds já estão carregados: não é uma medição de início do processo. O caso
dense tem 2.501 polígonos sintéticos. Não mede latência GUI ou memória nativa.
Veja [desempenho](performance.md) e [relatório bruto](performance/projected-paths.json).

O orçamento anterior era 8 MiB. Na base original SP de 892.336 posições, ele expulsava entradas durante o próprio percurso. O orçamento atual retém 14.455.285 bytes/702 entradas, sem mudar floats/paths; composição de pan novo de 9,09 para 0,41 s. [Medições e limites](performance-acceptance.md).
