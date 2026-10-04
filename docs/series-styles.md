# Séries, ciclos e folhas de estilo

## Uma chamada, vários traçados

```python
import azimlib as azl

fig, ax = azl.subplots(layout='constrained')
ax.states(facecolor='#eeeeee', linewidth=0.35)
lon = [-52, -49, -45]
a = [-25, -23, -20]
b = [-24, -22, -19]
first, second = ax.plot(lon, a, '--', lon, b, ':', label='Trajetos')
ax.legend([first, second], ['Trajeto A', 'Trajeto B'])
second.set(linewidth=1.2, visible=False)
fig.savefig('trajetos.svg')
```

`plot(lon, lat, [fmt], lon2, lat2, [fmt2], ...)` devolve um handle por série.
Os handles têm edição, ownership e remoção independentes. Uma matriz 2D tem
linhas correspondendo a posições e colunas correspondendo a séries:

```python
lines = ax.plot(lon, list(zip(a, b)), label=['A', 'B'])
line, = ax.plot('longitude', 'latitude', data={
    'longitude': lon, 'latitude': a,
})  # Rótulo padrão: latitude.
```

Vetores podem ser compartilhados com matrizes; duas matrizes precisam de
colunas compatíveis. Listas, tuplas, iteráveis e arrays NumPy funcionam, sem
exigir NumPy no runtime. Labels são escalares ou têm um valor por série de
cada grupo, como no contrato selecionado da referência. `data=` admite uma
chamada de até três argumentos com acesso por nome; múltiplos grupos com
`data=` são rejeitados explicitamente. A string encontrada em `data` prevalece
como coluna no segundo argumento, inclusive nomes como `o`.

Formatos e aliases comuns funcionam; kwargs prevalecem sobre tokens redundantes
de formato, com warning. Há suporte aos formatos de cor hex e aos nomes comuns
documentados pelo parser; não se promete todos os tokens/cor-specs Matplotlib.
Entradas escalares, séries vazias e com um ponto são válidas. `lon=`, `lat=` e
`fmt=` conservam a conveniência geográfica anterior para um grupo.

Diferença deliberada: `ax.plot([(lon, lat), ...])` continua significando uma
série de coordenadas geográficas. No Matplotlib, uma matriz passada sozinha
representa colunas de Y. Na Azimlib, use os dois argumentos para matrizes de
séries. Um vetor numérico sozinho usa índices de linha como longitude; essas
coordenadas ainda são geográficas, sem converters de datas/unidades.
Coordenadas não finitas, máscaras e gaps NaN não são suportados; latitudes
fora de ±90° são rejeitadas. A conveniência antiga de formato com apenas
marcador conserva linewidth zero, uma diferença da Line2D da referência.

Todas as formas, coordenadas, labels e estilos são preparados antes de anexar
camadas ou avançar o ciclo. Erro num grupo posterior não altera camadas,
limites, stale ou posição do ciclo. No experimento registrado, ambas as
bibliotecas anexaram zero linhas após erro de forma posterior; Matplotlib
consumiu a primeira cor e Azimlib a preservou. Não há rollback universal de
callbacks do usuário ou de lotes entre Artists diferentes.

## Ciclos próprios de propriedades

```python
ax.set_prop_cycle(
    color=['#d62728', '#2ca02c', '#1f77b4'],
    linestyle=['-', '--', ':'],
    marker=['o', 's', '^'],
)
ax.plot(lon, list(zip(a, b)))

cycle = azl.cycler(color=['red', 'blue']) + azl.cycler(linewidth=[0.8, 1.2])
ax.set_prop_cycle(cycle)
```

`cycler(key, values)` e `cycler(**properties)` criam ciclos finitos. `+` combina
linhas correspondentes de ciclos com o mesmo comprimento; `*` forma produto
cartesiano. As propriedades precisam ser distintas nas combinações. Iteração,
`keys` e `by_key()` não expõem os dados internos para edição. Aliases são
normalizados; duplicação de uma propriedade por alias é rejeitada. Também se
aceitam iteráveis finitos de dicionários, incluindo Cycler genérico fornecido
pelo usuário, sem importar a biblioteca cycler.

São propriedades de linha suportadas: color, linewidth, linestyle, marker,
markersize, markerfacecolor, markeredgecolor, markeredgewidth, alpha, caps,
junções, antialiased e zorder. Cores curtas e RGB/RGBA em [0,1] são convertidas
para hex. Não há suporte integral a todos os métodos/algebra do Cycler externo,
nem a qualquer propriedade de Patch/Collection no ciclo.

O ciclo avança quando precisa preencher uma propriedade ausente. Uma cor
explícita não consome um ciclo apenas de cores. Defaults explícitos de formato
participam dessa decisão. Scatter usa um cursor independente e somente a cor
do ciclo; `c=` numérico ou cor explícita não consomem esse cursor.
`set_prop_cycle()` afeta séries futuras; não recolore Artists existentes.
`set_prop_cycle(None)` retoma o rcParam atual. Cada Axes captura
`rcParams['axes.prop_cycle']` ao nascer; `clear()` recaptura os padrões atuais.

## Estilos empilhados e arquivos locais

```python
with azl.style.context(['dark_background', 'routes.mplstyle']):
    fig, ax = azl.subplots()
    ax.plot(lon, a, label='Trajeto')
    ax.legend()
```

`style.use()` aplica nomes, mappings, caminhos locais ou uma lista ordenada
desses itens. Itens posteriores prevalecem; toda a lista é validada antes de
alterar rcParams. `style.context()` restaura o estado mesmo quando o corpo
levanta erro; `after_reset=True` começa pelos defaults. Alterar o estilo global
não refaz automaticamente Artists já existentes.

`style.read(path)` lê UTF-8/BOM, linhas `rcParam: valor` e comentários. Um exemplo
de folha compartilhável com a referência está em
[routes.mplstyle](../examples/styles/routes.mplstyle). Use aspas duplas em cores
hex para que Matplotlib também preserve o `#` dentro de expressões de ciclo:

```text
lines.linewidth: 0.8
axes.grid: False
axes.prop_cycle: cycler('color', ["#d62728", "#1f77b4"]) + cycler(marker=['o', 's'])
```

O parser próprio interpreta literais e chamadas restritas de cycler, com `+`
e `*`; não executa Python. Não permite imports, atributos, chamadas arbitrárias,
URLs ou downloads implícitos. Apenas rcParams suportados são aceitos. Chaves
desconhecidas, duplicadas ou inválidas produzem erro com arquivo/linha; difere
da tolerância por warnings de folhas da referência. Temas científico/urbanos,
style discovery por diretórios e rcParams completos ainda não estão disponíveis.

Legendas herdam o fundo dos Axes pelo padrão `legend.facecolor='inherit'`.
`legend.edgecolor` e `legend.framealpha` também são configuráveis; kwargs
prevalecem. Textos de legenda conservam cor/família de fonte do momento de
criação mesmo se materializados depois de sair do contexto. Legendas não são
regeneradas implicitamente ao editar/ocultar linhas; reconstrua com `legend()`
quando desejar novas entradas, como no exemplo. Componentes cartográficos e
grade permanecem opcionais. O tema não configura automaticamente todo ornamento.

## Referência e integração

[Contratos registrados](series-styles-reference.json) com Matplotlib 3.11.2/Agg
comparam vários grupos, broadcasting de matrizes, nomes, ciclos combinados,
formatos, cursor de pontos, contexto/reset, folha local e defaults de legenda.
As cores dos estados são normalizadas apenas para comparar grafias RGB/hex.
Há 21 regressões/44 subtests adicionais; NumPy é opcional no teste de arrays.

[Exemplo](../examples/series_styles.py): fronteiras reais Natural Earth,
trajetos/estações sintéticos, temas claros e escuros,
[antes/depois](../gallery/series-light-after.png),
[escuro](../gallery/series-dark-after.png) e comparações independentes com
[Agg claro](../gallery/series-light-comparison.png) e
[Agg escuro](../gallery/series-dark-comparison.png). Escala/norte são adicionados
explicitamente pela Azimlib e não têm equivalente direto no núcleo Matplotlib.
PNG/SVG são estáticos, HTML separado; métricas/layout ainda diferem.
A legenda consulta estilos atuais dos handles. Desde o lote de
[texto/formatação](numeric-formatting.md), ao reconstruir a legenda ela copia
a visibilidade do símbolo: uma linha oculta mantém o texto e perde o símbolo,
como na referência. A visibilidade posterior da camada não altera essa cópia.
Ainda há diferenças na atualização de estilos e nos handlers; não se declara
o sistema completo de handles equivalente ao Matplotlib.

[Smoke Tk](../tools/smoke_series_tk.py), [source](series-tk-validation.json) e
[wheel](series-tk-wheel-validation.json) conferem 12 cenários com UI real oculta,
edição agrupada, 48 colunas sintéticas, limites compartilhados e histórico.
Não são benchmark, conferência visual do SO ou validação de base urbana densa.
Os critérios da [0.2.0](release-0.2.md) continuam parcialmente implementados.
