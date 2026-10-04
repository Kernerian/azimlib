# Cobertura raster de vistas novas

O perfil de uma vista de 645 municípios de São Paulo identificou caps/junções
arredondados como o principal custo. Foram mantidos os mesmos vértices,
supersampling, recortes, espessuras e regras de composição. Este lote:

- calcula o centro da elipse uma vez, em vez de repetir o cálculo por vértice;
- descarta discos inteiramente fora do mask antes de gerar sua geometria;
- obtém limites de coordenadas com `itemgetter`/`map`, preservando os valores;
- materializa os termos da área antes de `sum`, mantendo sua ordem e aritmética.

Uma tentativa de copiar arcos convexos em bloco foi rejeitada por não mostrar
ganho no benchmark. O recorte de polígonos continua o algoritmo próprio anterior,
também para geometrias côncavas e auto-interseções. Nenhuma dependência foi adicionada.

## Como reproduzir

```bash
python tools/compare_municipal_strokes.py /caminho/base.geojson --output municipal.json --repeats 2
```

O arquivo é fornecido explicitamente pelo usuário; a ferramenta não baixa dados.
A [proveniência da amostra](real-geojson-provenance.json) e os limites da malha
generalizada da API estão no [lote anterior](larger-batch.md). A base não faz parte
do pacote. O snapshot `tools/baselines/municipal-stroke-before/coverage.py` é
código próprio de desenvolvimento, excluído do wheel de runtime.

Cada vista usa a mesma cena nos dois modos. Chamadas são seriais, em ordem
alternada; tempo exclui composição, hashes, encoding PNG e I/O. Não há profiling,
Tk ou cache de frames durante o benchmark. Os hashes RGBA e PNG de todos os
renders são comparados, e os relatórios registram código, ferramenta e dados.

Regressões em `tests/test_municipal_stroke.py` cobrem áreas com comparação de bits,
polígonos irregulares/côncavos, discos subpixel/fora do mask/limites invertidos,
acúmulo de cobertura, alpha, recortes, caps/junções e três fatores de exportação.

## Limites

Medições locais source em 100 DPI, dois renders por modo/vista:

| Vista | Antes (s) | Depois (s) | Redução da mediana |
|---|---:|---:|---:|
| Completa | 19,264 | 17,522 | 9,0% |
| Foco | 3,006 | 2,565 | 14,7% |
| Pan | 3,533 | 3,302 | 6,5% |
| Zoom | 1,162 | 1,024 | 11,9% |

Os 16 renders preservaram RGBA e PNG. Valores brutos e hashes estão em
[municipal-stroke-source.json](municipal-stroke-source.json).

A suíte cumulativa passou com **583 testes/8.135 subtests**, incluindo quatro
regressões/1.087 subtests novos. Os oito scripts Tk também passaram novamente
no wheel instalado, sem Matplotlib/GIS: [registro](municipal-raster-tk-wheel.json).
São widgets reais ocultos, com entradas programáticas; não inspeção visual
da janela ou input físico.

O [wheel instalado](municipal-stroke-wheel.json) repetiu as quatro vistas com
um render por modo/vista, sem importar o checkout como runtime. Os oito renders
também preservaram RGBA/PNG; seus hashes coincidem com os do source. Os tempos
dessa rodada única não são combinados com as medianas acima.

Esses relatórios registram o lote anterior. A implementação exata medida está
preservada em `tools/baselines/stroke-kernels-before/coverage.py`; o código atual
recebeu kernels adicionais depois. Os tempos antigos não são atribuídos a eles.

As amostras locais são pequenas e sujeitas à carga da máquina. Não comprovam
fluidez, latência física ou ganho em todo tipo de mapa. O tempo inicial continua
alto em dados densos. O cache de vistas já visitadas é uma otimização separada;
`savefig()` permanece estático e `show()` continua usando o viewer próprio.
O [critério de desempenho da 0.2.0](release-0.2.md) permanece parcial.
