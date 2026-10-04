# Navegação compartilhada no HTML portátil

O viewer exportado usa um modelo JavaScript próprio, sem DOM no núcleo e sem
framework cartográfico. O HTML contém dados, fontes, SVG e scripts; pode ser
aberto offline, sem servidor ou processo Python. Matplotlib é somente a
referência de desenvolvimento para limites, aspecto e histórico.

```python
import azimlib as azl

fig, axs = azl.subplots(1, 2, sharex=True, sharey=True,
                       subplot_kw={'projection': 'mercator'})
for ax in axs:
    ax.map('brazil')
    ax.states(facecolor='none', linewidth=0.5)
axs[0].set_title('Político')
axs[1].rivers(color='steelblue', linewidth=0.6)
axs[1].set_title('Hidrografia')
fig.savefig('atlas.png')
fig.show(backend='browser', path='atlas.html')
```

Grade, legenda, colorbar, escala, norte, rosa e overview continuam opcionais.
Este exemplo não adiciona nenhum desses componentes. `savefig()` exporta a
composição Python sem UI; `show(backend='browser')` oferece a navegação portátil.

## Limites, aspecto e histórico

- Pan, zoom retangular, roda, duplo clique e atalhos atualizam os irmãos dos
  grupos `sharex`/`sharey`. Os modos `'all'`, `'row'`, `'col'`, vínculos manuais
  e mosaicos aninhados conservam seus grupos na exportação.
- `x` e `y` restringem a dimensão de uma ampliação. Longitude e latitude são
  sincronizadas separadamente; a outra dimensão conserva os limites locais.
- O histórico pertence à Figure inteira. Home restaura todos os painéis;
  Back/Forward restauram uma fotografia de todas as vistas. Uma nova alteração
  após Back descarta o ramo futuro. Cancelar um gesto restaura todos os irmãos
  sem inserir uma vista no histórico.
- A projeção mantém uma única escala espacial por painel. Compartilhar somente
  uma dimensão pode reduzir a largura/altura da moldura dentro da área nominal;
  o mapa não é esticado. Clipping, fundo, spines e âncoras de títulos/rótulos
  acompanham essa moldura. Ticks e grid cilíndricos são recalculados.
- Um overview explicitamente adicionado mostra o foco corrente com borda preta;
  clicar nele reposiciona o grupo. Nenhum minimapa aparece por padrão.

Mercator e equiretangular contínuas permitem o vínculo portátil, inclusive
entre projeções distintas: os irmãos recebem intervalos geográficos, projetados
individualmente. A navegação respeita a interseção dos domínios de latitude e
longitude do grupo, incluindo o limite polar de Mercator e a posição da emenda.
Índices de eixos ocultos/colorbars não confundem a identificação dos mapas.
Vínculos entre Figures distintas não são transportados ao arquivo HTML.

## Exportação da vista corrente

Salvar na toolbar exporta somente o canvas atual em SVG ou PNG, sem controles.
No PNG do browser, retângulos preenchidos sem transformação/borda são alinhados
aos mesmos limites de pixel para evitar frestas entre faixas adjacentes da
colorbar. O fundo percentual da Figure é preservado. SVG e o renderizador PNG
Python conservam seus próprios caminhos de exportação.

## Limites desta implementação

O HTML navega geometrias já projetadas; não recompõe toda a cena Python. Não
reexecuta callbacks Python, busca de rótulos, posicionamento automático de
legendas ou solver de layout durante o gesto. Em mapas cilíndricos contínuos,
a escala agora recalcula a distância e seus rótulos usando métricas próprias
exportadas da fonte. Norte e rosa mantêm tamanho físico e ancoragem na moldura;
nessas duas projeções o norte local é vertical. Para um mapa final com toda a
composição recalculada, ajuste os limites em Python e use `fig.savefig()`.

A escala automática escolhe uma distância legível; a escala de comprimento
explícito conserva esse comprimento. Se não couber na vista ampliada, é
ocultada com aviso na área de coordenadas, em vez de produzir uma medida falsa;
Home restaura a composição inicial. Não se reduz a fonte para amontoar números:
há três graduações, duas ou uma legenda compacta com total/unidade. A caixa
compacta remove a linha ausente e conserva somente uma folga curta.

Em outras projeções ou vistas descontínuas, escala, norte e rosa continuam
ocultos após navegar até Home. Regeneração/rotação local geral nesses casos
continua pendente. Nenhum desses componentes é acrescentado automaticamente.

Mapas isolados em outras projeções conservam a navegação afim da cena inicial.
Um grupo contendo projeção não suportada ou extensão descontínua é recusado
com mensagem no viewer, sem modificar parcialmente os irmãos. Não há ainda
vínculo geográfico portátil geral para projeções cônicas, globos ou subclasses
customizadas. O browser conserva toda a geometria exportada, sem índice espacial
dinâmico para bases densas. A GUI Tk real ainda exige validação em um ambiente
com Tcl/Tk funcional; os testes headless não substituem essa validação.

## Exemplos e verificação reproduzível

[Atlas vinculado](../gallery/linked-navigation.html) reúne político, rios,
valores sintéticos e rotas; adiciona colorbar e overview explicitamente.
[Grupos por linha/coluna](../gallery/linked-groups.html) mostra a alteração
independente das dimensões. O código está em
[portable_navigation.py](../examples/portable_navigation.py).
O [exemplo de componentes](../gallery/portable-components.html) mostra escala,
norte e rosa independentes em dois mapas vinculados, com km e milhas; veja
[portable_components.py](../examples/portable_components.py).

O oracle [portable-navigation-reference.json](portable-navigation-reference.json)
registra oito estados de Matplotlib 3.11.2/Agg: vistas, caixas, cursor e tamanho
do histórico. A comparação executa o modelo JavaScript realmente distribuído,
com casos adicionais de 36 combinações de grupos, projeções diferentes, domínios,
DPI, cancelamento, índices ocultos e operações inválidas sem alterações parciais.
Node é uma ferramenta opcional de teste, sem dependência no pacote Python.

Uma ferramenta de desenvolvimento testa 20 cenários em Chromium headless,
num contexto novo sem perfil pessoal. Instale Playwright separadamente para
esse teste; use `AZIMLIB_BROWSER_EXECUTABLE` para selecionar um Chromium local
ou deixe a variável ausente para usar o browser instalado pelo Playwright:

```bash
python examples/portable_navigation.py
python examples/portable_components.py
node tools/verify_portable_browser.js /caminho/para/artefatos
python tools/check_browser_png.py /caminho/para/artefatos
```

A conferência de PNG usa Pillow somente no desenvolvimento. Verifica o fundo
branco opaco deste exemplo e uma linha de pixels internos da colorbar, excluindo
a borda externa. É uma regressão específica, não uma promessa de igualdade de
pixels com Agg em todos os estilos, tamanhos ou browsers.

O modelo de componentes distribuído também é comparado numericamente com 147
composições do renderizador Python próprio: duas projeções, três unidades,
quatro cantos, três larguras, dois DPI e comprimentos explícitos. Métricas de
fonte, baseline, frame, distância, redução de graduações e recusas são cobertas,
além de oito deslocamentos de orientação e formatação numérica. Matplotlib não
possui esses ornamentos cartográficos no núcleo; a referência geométrica aqui
é o comportamento cartográfico próprio da Azimlib.
