# Rótulos cartográficos

Outputs under `gallery/` are local generated previews, not distributed assets.
For versioned current images, see the [0.3 gallery](gallery-0.3.md).

`ax.labels` é uma extensão cartográfica da Azimlib. Retorna uma camada editável,
com `set(...)`, `set_visible(...)`, `get_visible()` e `remove()`. Não é uma
alegação de que Matplotlib ofereça esse mesmo posicionador geográfico.

```python
import azimlib as azl

fig, ax = azl.subplots(projection='mercator', layout='tight')
ax.map('brazil', facecolor='white')
rivers = ax.rivers(color='#287fb0', linewidth=.6)
names = ax.labels(rivers, field='name', placement='line', fontsize=8,
                 color='#175477', halo='white', halo_width=2, padding=3)
ax.set_title('Hidrografia')
fig.savefig('rivers.svg')
azl.show()
```

O dado pode ser uma camada geométrica, um GeoJSON ou um objeto aceito pelo leitor
GeoJSON. O campo `field` determina o texto. Features sem geometria ou com nome
ausente/vazio não reservam espaço. A camada de rótulos é independente da camada
de rios: ocultar uma delas não oculta automaticamente a outra.

## Posicionamento e direção

- `placement='auto'` usa a direção local em LineString/MultiLineString e uma
  posição geométrica em pontos/polígonos.
- `placement='line'` exige geometrias lineares. Procura trechos visíveis, com
  comprimento suficiente e sem curvas muito fechadas. Funciona mesmo quando
  o centro original da linha está fora da vista.
- `placement='point'` mantém o posicionamento pontual, inclusive em linhas.
- `rotation=...` explícito prevalece sobre a direção automática. Ângulos
  públicos positivos são anti-horários, como nos demais textos da biblioteca.

A direção do nome não depende da ordem dos vértices. Um bloco de texto segue
um trecho aproximadamente reto; ainda não há texto curvado glifo a glifo.
Linhas são partidas no antimeridiano, densificadas e projetadas com o núcleo
próprio antes de buscar candidatos. Recorte, tamanho da fonte, halo e fundo
entram na avaliação. Nomes em polígonos só são aceitos se a caixa inteira
couber na área, sem cruzar a borda ou um buraco. A busca ainda é heurística;
nem toda região estreita ou geometria complexa terá um nome colocado.

## Colisões e prioridade

`avoid_overlap=True` é o padrão. As prioridades são globais entre camadas de
rótulos: maior valor primeiro, mantendo ordem estável em empates.

```python
names = ax.labels(cities, field='name', priority_field='importance',
                  fontsize=9, leader=True, padding=2)
names.set(fontsize=10, color='#222222')
names.set_visible(False)
fig.canvas.draw_idle()
```

`priority_field='priority'` lê a propriedade por feature; se ela estiver
ausente/nula, usa `priority=0` do estilo. `priority_field=None` ignora o atributo
e permite prioridade constante por camada. Valores precisam ser finitos.

Marcadores, textos explícitos, annotations (texto e setas), legenda, escala,
norte/rosa, overview e insets visíveis reservam espaço. Ocultá-los libera esse
espaço no próximo desenho. `set_in_layout(False)` apenas exclui um artista
do cálculo de margens; ele continua sendo um obstáculo se estiver visível.
Linhas de rios, preenchimentos de regiões e grade não reservam toda sua área.

`offsets=[(dx, dy), ...]` oferece deslocamentos candidatos em pixels lógicos
do canvas a 100 DPI; X cresce para a direita e Y para baixo. `padding` também
usa esses pixels. Sem offsets explícitos, pontos procuram posições vizinhas
e linhas procuram posições sobre o trecho e em suas duas laterais.
`leader=True` desenha uma linha entre o rótulo deslocado e sua âncora.
Essas linhas ainda não têm resolução própria de colisões entre si.

`avoid_overlap=False` libera sobreposições com outros artistas; não ignora
os limites da vista nem permite que nomes de polígonos cruzem suas bordas.
Features omitidas por falta de espaço permanecem na camada original.

## Visibilidade por extensão e zoom

```python
detail = ax.labels(cities, max_span=12, min_span=2)
ax.set_extent((-64, -52, -8, 0))  # west, east, south, north
fig.savefig('detail.png', dpi=150)
```

O span é `max(east-west, north-south)`, em graus geográficos. O intervalo é
inclusivo: `min_span <= span <= max_span`. `min_span=0` e `max_span=None`
não restringem a extensão. Isso é um controle de detalhe por vista; não é
denominador de escala física, pois projeção, latitude e tamanho da figura
também influenciam a escala. Ocultar por span não muda `get_visible()`.

Salvar ou desenhar em Python e navegar no desktop Tk recalcula candidatos,
colisões e direção usando o viewport corrente. O HTML portátil navega a cena
exportada: não refaz a busca, não aplica os filtros de span novamente nem
comunica alterações ao Python. Para uma saída final correta em outra vista,
altere os limites em Python e exporte novamente.

## Exemplos e limites

`python examples/labels.py` gera Brasil (`gallery/labels-brazil.png`, generated locally),
Amazônia (`gallery/labels-amazon.png`, generated locally), foco (`gallery/labels-focus.png`, generated locally)
e obstáculos (`gallery/label-obstacles.png`, generated locally), com versões SVG e HTML.
Limites e hidrografia são dados Natural Earth generalizados; o exemplo não
atribui classes de navegabilidade. Pontos de teste e a posição aproximada
de Manaus são identificados no código/figuras.

Próximas extensões: textos curvados, posições ótimas para polígonos, repetição
de nomes em linhas longas, exclusão entre leaders, estilos por atributo e
índices/cache para bases densas. Colisões entre rótulos automáticos de mapas
diferentes são resolvidas por Axes, não globalmente entre figuras/insets.
