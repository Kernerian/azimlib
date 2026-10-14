# Grafos e roteamento próprios — desenvolvimento da 0.4.0

Esta capacidade pertence ao checkout de desenvolvimento. A versão publicada e
a metadata estável continuam **0.3.0**. Não há serviço externo, download, tráfego
ao vivo ou motor GIS/roteador de terceiros por baixo desta API.

```python
import azimlib as azl

catalog = azl.DatasetCatalog("optional-data/urban-sao-paulo-1.0/catalog.json")
graph = azl.RoadGraph.from_catalog(
    catalog, "urban-sao-paulo", profile=azl.RoutingProfile("foot")
)
route = graph.route((-46.639, -23.545), (-46.638, -23.544),
                    objective="time", snap_radius_m=100)

fig, ax = azl.subplots()
ax.geojson(catalog.load("urban-sao-paulo"), edgecolor="gray", linewidth=0.5)
line = ax.route(route, color="red", linewidth=2, arrow=False)
line.set_picker(True)
ax.scale_bar()                 # componentes continuam opcionais
fig.savefig("route.svg")       # saída estática, sem UI
azl.show()                     # viewer próprio
```

As coordenadas acima são uma consulta dentro do extrato, não uma promessa de
conectividade entre quaisquer pontos. `RoutingError` informa ausência de rede,
ambiguidade ou rota inviável. O [exemplo reproduzível](../examples/local_routing.py)
seleciona extremos reais conectados do catálogo e exporta PNG/SVG com atribuição.
`import azimlib.pyplot as plt` continua disponível para a mesma API de figuras.

## Modelo, unidades e proveniência

- `RoadGraph` é imutável e específico de um `RoutingProfile`. Nós conservam IDs
  OSM e longitude/latitude WGS84; arestas dirigidas conservam ID de via, índice
  do segmento, sentido, atributos necessários e geometria entre nós consecutivos.
- `RoutingSource` exige origem pública/URN, versão, SHA-256, licença, copyright
  e atribuição; permite preservar avisos completos, copiados pelo catálogo.
  Reutiliza o contrato de origem do geocoder. O hash original
  é verificado nos bytes consumidos por `from_osm()`/`from_osm_index()`/catálogo.
  Em `from_records()`, a origem é uma declaração do fornecedor dos registros,
  não uma certificação automática de autoria ou do hash de um arquivo ausente.
- Comprimento e snapping usam esfera terrestre de raio **6 371 008,8 m** e arcos
  menores; distâncias em metros, duração em segundos, velocidades em km/h.
  Não representam levantamento elipsoidal, altitude, declividade ou trânsito.
- `RoadRoute.steps`, `instructions`, `distance_m`, `duration_s` e `to_features()`
  preservam origem e IDs. Instruções são manobras geométricas (`depart`,
  `continue`, `left`, `right`, `u_turn`, `arrive`), sem orientação por faixas,
  anúncios de voz, tempos de semáforo ou garantia de navegação viária legal.
- Rota estacionária tem geometria Point, zero distância e duração; não se
  inventa uma linha. O acesso entre posição consultada e snap fica separado em
  `NetworkSnap.distance_m`, sem acrescentar um trajeto off-road fictício.

## Conectividade e importação

`from_records()` recebe os `OSMRecord` próprios; `from_osm()` lê XML 0.6 limitado,
sem entidades/includes; `from_osm_index()` usa o índice PBF próprio em disco.
`from_catalog()` verifica arquivos e licença de catálogos OSM XML/PBF locais.
Não se reconstrói topologia por igualdade aproximada de coordenadas de GeoJSON.

A conexão exige **o mesmo ID de nó OSM**. Interseção geométrica, dois IDs na
mesma coordenada, ponte sobre rua e túnel sob rua não criam uma ligação.
`bridge`, `tunnel` e `layer` são preservados. Um nó explicitamente compartilhado
entre vias de níveis diferentes representa uma conexão mapeada, como uma rampa;
o motor não corrige silenciosamente um erro de mapeamento nesse nó. Referências
ausentes, IDs duplicados, segmentos nulos/antípodas e topologia de restrição
incompleta falham. Não há reparo, fabricação de conexões ou navegação em áreas
`highway` poligonais sem uma rede de eixos adequada.

## Perfis e regras suportadas

Perfis `car`, `bicycle`, `foot` têm allowlists de classes de via e velocidades
genéricas explícitas em `RoutingProfile.speeds_kmh`, editáveis na construção:

```python
profile = azl.RoutingProfile("bicycle", speeds_kmh={
    "cycleway": 20, "residential": 16, "path": 10
}, max_speed_kmh=25)
```

São hipóteses de modelagem, não padrões legais de um país. Classes não listadas
são excluídas. Hierarquia de acesso: `motorcar → motor_vehicle → vehicle → access`,
`bicycle → vehicle → access`, `foot → access`. Valores `yes`, `designated`,
`permissive`, `official` permitem; `no`, `private`, `destination`, `customers`,
`delivery`, `agricultural`, `forestry`, `use_sidepath`, `dismount` excluem
conservadoramente. Não se presume autorização de cliente/morador.

Mão única `yes/1/true`, `no/0/false`, `-1`, roundabouts e motorways implícitos,
e overrides `oneway:<mode>` seguem o perfil. Mão única genérica não é aplicada
a pedestres; `oneway:foot` é explícita. `maxspeed`, `maxspeed:forward/backward`
aceitam números em km/h e `mph`, limitando a velocidade estimada do perfil.
Muros/bloqueios são excluídos; bollards são permeáveis a pedestres/bicicletas,
outros obstáculos conhecidos têm política conservadora; gates sem permissão
explícita são fechados. Barreiras desconhecidas falham.

Relações `restriction`/`restriction:<mode>` interpretam `no_*`, `only_*`,
`no_entry/no_exit`, modos específicos e `except`. Suportam um nó `via` ou cadeia
ordenada de vias `via`, inclusive vias com vários segmentos. Múltiplos `from/to`
são aceitos para `no_entry/no_exit`. `no_u_turn` na mesma via diferencia retorno
de continuação. O estado da busca retém o histórico necessário, inclusive ao
passar por pontos intermediários e splits de snapping. Conversões obrigatórias
com destino/via inacessível falham explicitamente, sem ignorar a obrigação.

**Cobertura delimitada:** condicionais aplicáveis, sentidos reversíveis,
acesso direcional, velocidades simbólicas/por faixa, restrições por dimensão,
leis regionais implícitas, ferries, horários, trânsito, áreas navegáveis,
multimodalidade entre perfis e manobras de faixas não são um serviço completo de
navegação. Regras condicionais/direcionais reconhecidas, valores desconhecidos e
restrições de conversão não interpretáveis lançam `UnsupportedRoutingRule`;
não são descartados silenciosamente. Dimensões/carga não são modeladas pelo
perfil de carro, que não deve ser usado para caminhões/veículos especiais.

Semântica estudada a partir de fatos do formato e tags:
[restrições](https://wiki.openstreetmap.org/wiki/Relation:restriction),
[mão única](https://wiki.openstreetmap.org/wiki/Key:oneway),
[acesso](https://wiki.openstreetmap.org/wiki/Key:access),
[velocidade](https://wiki.openstreetmap.org/wiki/Key:maxspeed).
Não se incorporou código, snippets ou texto da implementação de outro roteador.

## Snapping e caminho ótimo

`graph.snap(point, radius_m=..., max_candidates=...)` projeta sobre o arco menor
mais próximo das vias acessíveis. Postings espaciais próprios selecionam
segmentos; a distância final é esférica. Empate em vias coincidentes/desconexas
é erro explícito: selecionar um ID de nó elimina a dúvida, sem adivinhar nível.
Inteiros de origem/destino são IDs de nós, pares são `(lon, lat)`; resultados do
geocoder com `.coordinate` também são aceitos. Snaps de outro grafo falham.

`graph.route(origin, destination, via=(...), objective="distance"|"time",
algorithm="astar"|"dijkstra")` divide arestas virtualmente em todos os stops,
respeitando sentido e custo proporcional, sem conectar vias paralelas. A busca
é global, com ordem dos stops no estado; não reinicia restrições a cada trecho.
A* usa limite inferior por distância esférica e maior velocidade efetiva da rede.
Dijkstra não usa heurística. Custos são estritamente positivos e não há custo
customizado arbitrário que invalide a prova de limite inferior.

## Persistência, recursos e execução interativa

`graph.save("graph-index")` cria diretório novo atomicamente, sem sobrescrever.
`graph.json` contém primitivas filtradas, perfil e avisos de origem completos;
`manifest.json` fixa schema, tamanho e SHA-256. `RoadGraph.load()` confere os
bytes e reconstrói os índices/arestas/restrições, sem confiar em custos derivados
serializados. Hash detecta alteração acidental, **não autentica um manifest
malicioso reescrito junto com os dados**. Symlinks de payload são rejeitados.

Limites explícitos: 250 mil primitivas/arestas, 64 MiB de registros JSON
filtrados, 100 mil estados de expansão/compilação de regras por padrão; 256
arestas por regra. Consulta: 250 mil estados descobertos/expandidos e entradas
de fila, 64 stops intermediários, 10 mil candidatos e 100 mil células de snap.
Persistência: 128 MiB por padrão com reserva de disco. Os limites de contagem/
bytes **não são um limite rígido de RSS**; objetos Python e índices usam memória
adicional. Overflow/cancelamento lança exceção sem alegar resultado parcial ótimo.
XML é limitado a 64 MiB. O grafo fica em RAM e não alega roteamento planetário.

Consultas síncronas podem custar tempo; use executor para preservar o event loop:

```python
from concurrent.futures import ThreadPoolExecutor
pool = ThreadPoolExecutor(max_workers=1)  # manter enquanto a consulta existir
task = graph.submit(pool, origin, destination, objective="time")

def poll():
    if task.done():
        task.draw(ax, color="red")        # thread solicitante/viewer
        fig.canvas.draw_idle()
        return False

timer = fig.canvas.new_timer(interval=30)
timer.add_callback(poll)
timer.start()                            # após abrir um viewer Tk/Qt
```

`task.cancel()` sinaliza cancelamento cooperativo; `task.result()` propaga o erro.
Workers não editam Artists; `task.draw()` exige o thread solicitante e um resultado
pronto. O executor é do chamador; a biblioteca não mantém um serviço oculto.
`route.playback(ax, frames=100, autoplay=False)` devolve `FuncAnimation` próprio
e `route_marker` editável. `seek()` funciona offline; playback automático usa o
timer do viewer. `sample(seconds)` interpola o tempo estimado, sem simular GPS.

## Licenças, privacidade e validação

Nomes públicos, IDs, tipo de via e regras de acesso/conversão são allowlisted.
Notas, contatos, identidades de editores, endereços residenciais e caminhos de
origem não são copiados ao índice; consultas não são registradas. O código é
original BSD 3-Clause; **bases e índices derivados OSM continuam sob ODbL**,
com copyright, atribuição e licença própria. Bases opcionais e índices gerados
não vão no wheel/sdist. Atribuição deve acompanhar mapas publicados pelo usuário.

[Testes](../tests/test_routing_040.py) usam redes originais, oráculo Floyd de
todos os pares, restrições conhecidas, vias desconexas, snapping global,
equivalência XML/PBF, corrupção/limites, persistência, executor e Artists.
[Ensaio](../tools/validate_routing.py): grade de 6 400 nós/25 280 arestas dirigidas,
40 consultas A*/Dijkstra, heartbeat durante worker, persistência e catálogo real
licenciado em três perfis. [Snapshot local](routing-validation-0.4.json) registra
hashes e medidas. Não substitui CI multiplataforma ou aceite nativo da release.

O ensaio respeita **20 GB gerados e 15 GB livres**; não baixa o planeta.
**2.08 permanece pendente exclusivamente pelo ensaio planetário integral** e
será revisitado antes do gate final, sem bloquear etapas independentes.
