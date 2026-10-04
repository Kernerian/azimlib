# Edição de coleções de pontos

`ax.scatter` retorna uma `ScatterCollection` própria, derivada de Layer/Artist.
Não usa PathCollection ou outro componente de Matplotlib como backend.

```python
import azimlib as azl
from azimlib.colors import Normalize

fig, ax = azl.subplots()
points = ax.scatter([-52, -48], [-25, -21], s=[36, 100],
                    c=[20, 80], norm=Normalize(0, 100))
points.set_offsets([[-54, -28], [-43, -18]])
points.set_sizes([64, 144])
points.set_array([30, 70])
ax.relim()
ax.autoscale_view()
fig.savefig('pontos.svg')
```

Offsets são pares longitude/latitude em graus, não deslocamentos em pixels.
Um par `(lon, lat)` também representa um ponto. A latitude deve estar entre
-90 e 90; posições precisam de números finitos. `get_offsets()` e `get_sizes()`
retornam cópias em listas, sem exigir NumPy ou permitir alterações silenciosas.

`s` e sizes são áreas em pontos². A conversão para o DPI de exportação acontece
na renderização. `set_sizes(sizes, dpi=72)` conserva essas unidades físicas; seu
argumento dpi não muda o tamanho físico da coleção. Diferentemente dos caches
internos de PathCollection, não existem transforms de marcador calculados pelo
setter. Um escalar em scatter é armazenado como `[s]`; set_sizes espera uma
sequência. Áreas negativas/NaN/infinito são rejeitadas; zero ou sizes vazio não
desenha marcador nem reserva obstáculo para labels.

## Quantidade de pontos e cores

Tamanhos e cores explícitas são repetidos ciclicamente ao desenhar a coleção.
O scatter inicial aceita s escalar ou um valor por ponto; posteriormente
set_sizes permite sequências de outros comprimentos, como PathCollection.
Dados numéricos de cores precisam continuar com um valor por ponto. Para mudar
quantidade e valores juntos:

```python
points.set(offsets=[[-52, -25], [-48, -21], [-44, -19]],
           sizes=[16, 64], array=[0, 50, 100])
azl.setp(points, offsets=[], sizes=[], array=[])
```

Uma mudança isolada de quantidade com array numérico incompatível é rejeitada
antes de alterar os pontos. Esta validação antecipada é própria: Matplotlib
permite certas inconsistências temporárias entre setters até o desenho.
Também aceitamos `[]` para offsets vazios; Matplotlib requer um array com forma
`(0, 2)` nesse caso. Sem dados numéricos, cores explícitas continuam ciclando;
use `set_array(None)` para retirar o mapeamento escalar.

Campos inválidos de offsets, sizes, array ou estilos são validados antes de
alterar dados e visibilidade. Não há transação geral entre vários Artists,
normalizadores, callbacks ou objetos externos. Edições notificam os owners;
setp/set agrupa a notificação de Artist. Colorbars acompanham alterações
numéricas e a norm compartilhada, mantendo seu intervalo até autoescala explícita.
O lote set/setp desta coleção aceita offsets, sizes, array e estilos; para
norm/cmap/clim use os setters dedicados. A revisão geral de propriedades de
coleções continua no escopo de 0.2.0.

## Cena, legenda e vista

Cena, obstáculos de labels e colocação de legenda consultam as mesmas áreas,
cores e bordas atualizadas. linewidth define a largura da borda de scatter;
markeredgewidth explícito prevalece. A legenda atual usa um marcador de área
representativa, não uma escala automática de várias bolhas proporcionais.

Edição de offsets não move a vista: relim/autoscale_view recompõe eixos
automáticos, mantendo limites manuais. Veja [normalização e limites](norm-limits.md).
remove/clear desliga a coleção da figura; visibilidade e callbacks seguem
o [protocolo de Artists](artists.md). O HTML continua uma cena exportada.

Picking, offsets projetados, símbolos individuais, máscaras NumPy/RGBA,
legendas automáticas de tamanho e atualização incremental ainda estão pendentes.
Veja o [exemplo antes/depois](../examples/scatter_editing.py). Seis casos foram
comparados diretamente com Matplotlib 3.11.2/Agg em
[scatter-reference.json](scatter-reference.json).
