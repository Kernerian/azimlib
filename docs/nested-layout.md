# Subdivisão de painéis e mosaicos aninhados

Três avanços integrados: GridSpecFromSubplotSpec/subgridspec, mosaicos
aninhados e composição automática de uma hierarquia. Toda alocação/medição
pertence à Azimlib; Matplotlib é apenas uma referência de desenvolvimento.

## Grids filhos

```python
import azimlib as azl

fig = azl.figure(figsize=(11, 8), layout='constrained')
root = fig.add_gridspec(1, 2, width_ratios=[1.3, 1])
main = fig.add_subplot(root[0], projection='mercator')
detail = root[1].subgridspec(2, 2, height_ratios=[1, 1.2])
north = fig.add_subplot(detail[0, 0])
east = fig.add_subplot(detail[:, 1])
south = fig.add_subplot(detail[1, 0])
```

subgridspec divide o retângulo nominal da seleção pai. Retorna
GridSpecFromSubplotSpec, que também pode ser construído diretamente com
(nrows,ncols,subplot_spec). Pesos, slices retangulares, spans, subplots e
consultas de posições seguem o GridSpec existente. Outro subgridspec pode
subdividir uma seleção do filho. get_topmost_subplotspec retorna a seleção
original no grid raiz, como a referência.

Em layout manual, o filho usa margens do pai; wspace/hspace explícitos são
locais. Quando omitidos, herdam os parâmetros da Figure, como a referência,
e não overrides de espaçamento do grid pai. get_subplot_params/posição são
nominais; não medem o viewport corrigido pelo aspecto cartográfico.
subplots_adjust e root.update reposicionam descendentes. Alterar pesos
marca stale, mas em modo manual exige update() ou subplots_adjust para
aplicá-los às posições existentes, conforme o contrato do GridSpec.

child.update(wspace=...,hspace=...) é uma conveniência própria: edita seus
espaçamentos e aplica pesos. Matplotlib não expõe esse update no grid filho.
Margens left/right/top/bottom do filho são rejeitadas; pertencem ao pai.
Nenhum grid pode ser reutilizado em outra Figure. Vincular uma seleção de
uma hierarquia sem Figure vincula também os grids ancestrais à mesma Figure.
subplot(121) procura grids raiz; use subplot(child[0]) para selecionar um filho.

## Mosaicos aninhados

```python
fig, maps = azl.subplot_mosaic(
    [['Brasil', [['Sudeste', 'Nordeste'], ['Sul', 'Nordeste']]]],
    figsize=(12, 9), layout='constrained', width_ratios=[1.3, 1],
    subplot_kw={'projection': 'mercator'},
    per_subplot_kw={'Nordeste': {'projection': 'equirectangular'}})
maps['Brasil'].map('brazil')
maps['Sudeste'].state('SP')
maps['Sul'].state('RS')
fig.savefig('atlas.svg')
```

Uma célula contendo uma **lista 2D de linhas** cria um grid filho nessa célula.
Os nomes são globais no dicionário retornado; repetir um nome em layouts
distintos é rejeitado antes de criar eixos. Dentro de cada grid, um nome
repetido ainda precisa formar um retângulo. Vazios, seleção explícita de
mapas, projeções por nome e estilos dos handles conservam os contratos
anteriores. A ordem percorre as células pela primeira ocorrência, entrando
em um grupo filho ao encontrá-lo, como os casos da referência.

gridspec_kw/width_ratios/height_ratios da chamada configuram o grid raiz.
Filhos começam com pesos iguais e gaps herdados em modo manual; edite-os
pelos handles de get_gridspec. per_subplot_kw usa nomes globais, inclusive
de níveis internos. As listas/dicionários originais não são modificados.
Aninhamento por listas é validado até 64 níveis; ciclos/profundidade excessiva
são rejeitados explicitamente. Tuplas hashable continuam sendo nomes da
Azimlib, não contêineres de mosaicos filhos.

## Composição automática

Tight/constrained aceitam uma hierarquia com um único grid raiz. O caminho
anterior para grids simples permanece. Na hierarquia, o solver distribui
trilhas por pesos, reserva margens para títulos/ticks/rótulos e mede até 16
vezes. Grids filhos reservam espaço de decoração dentro de sua seleção pai;
grupos distintos podem ter margens internas diferentes. Esse solver próprio
não promete posições idênticas às do layout automático do Matplotlib.

Colorbars que abrangem mapas em vários níveis reservam espaço no ancestral
comum. Colorbars de um grupo filho também funcionam. Insets/ornamentos
continuam opcionais; componentes internos não participam de uma solução
universal de colisões dentro de cada mapa. Eixos manuais/cax ou excluídos de
layout conservam suas posições; o solver não os trata como obstáculos externos.
Eixos ocultos/removidos deixam de reservar espaço. Texto/pesos/tamanho da
Figure editados provocam nova medição no próximo desenho.

Se a figura for pequena ou não houver convergência, avisa e restaura todas
as posições/parâmetros anteriores. Isso não garante que um canvas minúsculo
possa ser renderizado: o compositor ainda pode rejeitar viewports insuficientes.
Múltiplos grids raiz independentes em layout automático, SubFigure
e compressed layout continuam pendentes. sharex/sharey e label_outer já estão
disponíveis; veja [eixos compartilhados](shared-axes.md). HTML é uma cena
exportada e não recalcula esse layout após navegação.

[nested_atlas.py](../examples/nested_atlas.py) demonstra Brasil e um grupo
de regiões, com colorbar do grupo, norte/compasso/escalas opcionais e edição
de pesos/títulos. O indicador é sintético. A [referência registrada](nested-layout-reference.json)
contém 10 posições manuais, quatro estados de atualização e três mosaicos,
obtidos de Matplotlib 3.11.2/Agg. compare_nested_layout.py gera comparação
visual de mapas com os mesmos dados/DPI; o pacote funciona sem Matplotlib.
