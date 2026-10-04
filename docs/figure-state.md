# Figuras, seleção de mapas e mosaicos nomeados

Três avanços relacionados aproximam a organização de mapas de pyplot:
registro por número/nome, seleção explícita do eixo ativo e subplot_mosaic.
O registro, a seleção, os grids, o layout e o desenho são próprios.
Matplotlib 3.11.2/Agg é usado somente nos tools de desenvolvimento;
[figure-state-reference.json](figure-state-reference.json) registra sete
estados de figuras, cinco estados de seleção e oito mosaicos.

## Figuras por número ou nome

```python
import azimlib as azl
import azimlib.pyplot as plt

fig = azl.figure(7, figsize=(8, 6))
ax = fig.add_subplot()
atlas = azl.figure('Atlas')
azl.figure(7)                 # Reativa fig, conservando seu conteúdo.
azl.figure('Atlas')           # Reativa a figura com esse label.
azl.get_fignums()             # Números ordenados.
azl.get_figlabels()           # Labels na mesma ordem dos números.
azl.fignum_exists('Atlas')
azl.close(7)
azl.close('Atlas')
```

Um novo número automático é max(0,números existentes)+1. Strings são labels,
não números convertidos: figure('7') é diferente de figure(7). Inteiros zero
ou negativos também são aceitos. figure(fig) reativa uma Figure registrada;
uma Figure construída diretamente, sem registro pyplot, é rejeitada.
get_fignums/get_figlabels retornam listas novas. Fechar uma figura ativa
retorna à última figura ainda registrada que foi ativada; close() sem nenhuma
figura e close de número/nome inexistente não criam outra figura.

Reativar com figsize/dpi/facecolor/layout emite aviso e conserva os valores
existentes. clear=True limpa o conteúdo da mesma Figure; preserva número,
label, tamanho/DPI e engine. fig.clear()/clf() fazem a mesma limpeza;
cla() limpa somente o eixo ativo. Barras são desconectadas e Artists removidos
não continuam marcando a Figure antiga como stale.

subplots/subplot_mosaic aceitam num e clear. Uma chamada em uma Figure já
existente acrescenta novos eixos; use clear=True para recomeçar. Não há
transação global para clear=True seguido de parâmetros inválidos.
Figure.set_label/get_label altera o nome; number conserva a identidade.
O título HTML padrão e o título da janela Tk usam Figure N: label.
Atualização de título foi testada com uma janela simulada, não uma sessão Tk
funcional neste ambiente. Não há manager/backends externos ou opções gerais
de pyplot.figure como FigureClass, monitor, forward e frameon.

## Eixo ativo e subplot

```python
fig, maps = azl.subplots(1, 2, num='Atlas')
other, other_ax = azl.subplots(num='Outra figura')
plt.sca(maps[0])              # Seleciona o eixo e reativa sua Figure.
plt.plot([-49, -47], [-23, -22], 'o--')
plt.title('Mapa selecionado')
plt.savefig('atlas.svg')      # Salva a Figure desse eixo.
```

fig.sca(ax) seleciona apenas dentro da Figure; plt.sca(ax)/azl.sca(ax)
selecionam também a Figure registrada. fig.gca()/gca() retornam o eixo
selecionado. A ordem pública Figure.axes continua sendo a ordem de criação.
Remover o eixo ativo restaura o último eixo selecionado ainda presente.
Seleção isolada não modifica a cena nem provoca desenho de dados.
Um inset filho não participa da seleção pyplot; use seu handle diretamente.
Um cax adicionado à Figure participa; após removê-lo, o eixo anterior é
restaurado. delaxes(ax) oferece remoção explícita.

plt.subplot(221), subplot(2,2,(3,4)) e subplot(gs[0]) reutilizam uma seleção
existente. Opções explícitas de projeção diferentes criam outro eixo.
Sem opções, a primeira seleção correspondente é reutilizada. Como na API
orientada a objetos do Matplotlib, Figure.add_subplot cria um novo eixo;
use pyplot.subplot para reuso. Eixos sobrepostos não são removidos
automaticamente. Somente projection/projection_kw são opções de subplot
nessa fundação; os dados continuam lon/lat, não eixos cartesianos arbitrários.

## Mosaicos de mapas

```python
fig, maps = azl.subplot_mosaic(
    [['Brasil', 'Brasil'], ['São Paulo', 'Amazonas']],
    num='Atlas', figsize=(10, 10), layout='constrained',
    height_ratios=[2, 1.4], subplot_kw={'projection': 'mercator'})
maps['Brasil'].map('brazil')
maps['São Paulo'].state('SP')
maps['Amazonas'].state('AM')
fig.savefig('atlas.png')
```

Figure.subplot_mosaic retorna somente o dicionário; a função de módulo
retorna (Figure,dicionário). Cada nome ocupa um retângulo contíguo em um
GridSpec próprio. A ordem dos nomes é sua primeira ocorrência, linha a linha.
Cada eixo recebe str(nome) como label; nomes hashable como números/None
funcionam em matrizes. A string 'AA;BC' equivale a duas linhas, com A ocupando
todo o topo. Strings multilinha também funcionam. '.' representa uma célula
vazia; empty_sentinel permite outro valor. Vazios não criam eixos.

width_ratios/height_ratios, gridspec_kw, layout tight/constrained e colorbars
compartilhadas/cax conservam seus contratos. Nenhum ornamento/grade aparece
automaticamente. subplot_kw define projection/projection_kw comuns;
per_subplot_kw sobrescreve esses parâmetros por nome. Tuplas de nomes aplicam
as mesmas opções a vários eixos. Em mosaicos escritos como string, 'BC' como
chave de per_subplot_kw aplica a B e C; em matrizes, um nome de várias letras
é uma chave única. Entradas originais são copiadas.

Nomes repetidos sem preencher um retângulo, opções/nome desconhecidos,
projeções inválidas e pesos inválidos são rejeitados antes de anexar eixos
ou grid. Mosaicos/grids aninhados também estão disponíveis; veja
[hierarquias](nested-layout.md). sharex/sharey também estão disponíveis; veja
[eixos compartilhados](shared-axes.md). SubFigure e CompressedLayout ainda não
são suportados. O solver continua limitado a uma hierarquia de um
grid raiz ativo por Figure; vários grids independentes funcionam em layout manual.
HTML continua uma cena exportada: edições Python exigem reexportação.

[figure_state.py](../examples/figure_state.py) gera um atlas Brasil/SP/AM
antes/depois, selecionando SP a partir de outra Figure e editando uma norm
compartilhada. As cores são dados sintéticos, sem interpretação estatística.
compare_mosaic.py gera uma referência visual Agg com os mesmos dados/DPI;
isso não significa igualdade de pixels nem de todo o layout automático.

Dimensões/DPI públicos e títulos laterais independentes são descritos em
[integração de composição](sizing-composition.md).
