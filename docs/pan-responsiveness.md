# Responsividade do pan — 2026-10-03

A revisão preserva a espessura durante o pan, melhora o renderer temporário
e corrige a continuidade do gesto ao sair e voltar ao canvas.

## Comparação medida

Tk real oculto; handlers sintéticos temporizados durante dois segundos; mesmo
Brasil, tamanho, dados, estilo e deslocamento. Inclui composição, raster e entrega
a PhotoImage. Cada execução abaixo ocorreu separadamente, antes de iniciar a
suíte/galeria pesada. Não mede input físico nem apresentação no monitor.

| Runtime | Quadros/s durante o gesto | Maior intervalo do timer Tk | Raster de navegação, mediana |
|---|---:|---:|---:|
| [Primeiro worker instalado](pan-responsiveness-before.json) | 0,44 | 883 ms | 1.263 ms |
| [Revisão anterior instalada](pan-responsiveness-previous-wheel.json) | 9,90 | 31 ms | 67 ms |
| [Azimlib atual source](pan-responsiveness-source.json) | 30,90 | 40 ms | 25 ms |
| [Azimlib atual instalada](pan-responsiveness-wheel.json) | 31,99 | 32 ms | 23 ms |
| [Matplotlib/TkAgg de referência](pan-responsiveness-reference.json) | 30,81 | 47 ms | — |

Tempos variam por hardware, carga e complexidade. Os limites finais
coincidem com a referência até arredondamento numérico. São execuções pontuais,
sem afirmar equivalência geral de FPS ou um SLA de responsividade.

Python 3.14.4/Windows, Pillow 12.3.0, aggdraw 1.4.1 e NumPy 2.5.3 no ambiente
atual. Os JSONs registram hashes dos módulos usados.

## Primeira pegada e retomada

[Antes](first-grab-before.json): primeiro quadro em 113 ms; nova pegada durante
o raster preciso em 1.082 ms. [Wheel atual](first-grab-wheel.json): 39 ms e
46 ms, respectivamente. [Source](first-grab-source.json) registra a mesma prova
independente. Essas medidas começam no Motion sintético e terminam na entrega
do buffer; não incluem latência de mouse/compositor. O processo de pixels aquece
durante o primeiro desenho, e a próxima pegada interrompe trabalho preciso
obsoleto. O teste confere o quadro final contra nosso renderer preciso.

## Implementação e independência

- Geometria, projeções, composição, estilos, construção de strokes, dashes,
  caps/joins, buracos e layout continuam próprios. Nenhum backend/asset
  Matplotlib ou biblioteca geoespacial é incorporado.
- O extra `gui` inclui **aggdraw e NumPy genéricos**. aggdraw preenche os
  polígonos de stroke que a Azimlib já calculou, com antialiasing, usando
  explicitamente um pen de largura zero para evitar a dilatação de contorno
  padrão do fill. Não delegamos a construção do traço. NumPy acelera a
  validação/comparação de todos os vértices para o cache.
- Um subprocesso próprio recebe somente Scenes congeladas por pipe privado e
  devolve RGBA. Não carrega Figure/Artists/Tk nem usa PNG como transporte. A
  rasterização temporária não disputa o GIL da thread de eventos Tk; o processo
  termina quando o viewer fecha. Não usa rede nem exige mudar o script do usuário.
- Uma Scene intermediária pode ser preparada enquanto o raster está ativo;
  demais movimentos guardam somente os limites mais recentes. Quadros de um
  gesto anterior são invalidados ao iniciar o seguinte.
- Coordenadas do cursor, antes do próximo desenho, usam bounds cilíndricos
  monotônicos quando disponíveis; outras projeções continuam no cálculo geral.
  Evita amostrar 1.225 pontos por Motion sem mudar coordenadas/fit. Seis casos
  conferem a vista ainda não pintada contra a Scene completa. O handler teve
  máximo de aproximadamente 2 ms nos benchmarks atuais.
- Tiles próprios de primitivas, nunca uma imagem do canvas transladada: clipping,
  ticks e ornamentos são compostos para a vista nova. LRU de 128 entradas,
  16 MiB de payload de pixels/arrays, tile RGBA individual até 8 MiB, arrays de
  preparação até 8 MiB por quadro. Overhead dos objetos Python é adicional.
  Todos os vértices são comparados antes de aceitar uma tradução; zoom, dados e
  estilo invalidam reutilização. Sem aggdraw há fallback para o kernel próprio.
- Glyphs/halos continuam amostrados a 3x e alinhados à grade de pixels; o cache
  das métricas portáteis de fonte é limitado e devolve cópias independentes.
  Dezesseis casos de largura/ângulo verificam área do traço temporário versus
  o preciso, incluindo linhas finas; cache e clips têm testes específicos.

O preenchimento genérico foi conferido diretamente no
[código oficial de aggdraw](https://github.com/pytroll/aggdraw/blob/main/aggdraw/_aggdraw.cxx).
Essa dependência opcional não é o Matplotlib nem um motor cartográfico.

## Bordas e qualidade final

Ao voltar com o botão já solto, um gesto cujo release foi perdido termina na
última posição realmente pressionada. A posição de reentrada não desloca o
mapa. Com o botão ainda pressionado, o gesto continua fora dos Axes, preservando
a origem congelada. Um zoom retangular interrompido não aplica uma seleção
incompleta. O histórico grava a vista uma vez.
[Integração source/wheel](pan-interaction.md) cobre esses casos.

Ao soltar, o quadro exato levou aproximadamente um segundo neste Brasil. Essa
espera ocorre fora da thread Tk e pode ser interrompida por outra pegada.
PNG/SVG estáticos usam o caminho normal; qualidade final e dimensões
continuam iguais às cenas completas. Navegação, ownership e exportação têm
regressões específicas, além dos smokes source/wheel.

A verificação visual Windows cobre espessura, componentes e navegação;
o [registro de observação](viewer-visible-acceptance.md) fecha 3.08–3.10.
Acelerar o quadro preciso e medir gesto físico visível continuam no
critério 4.09. Os benchmarks ocultos isoladamente não fecham esse item. O núcleo permanece
sem dependências obrigatórias e o extra `png` continua apenas Pillow.

## Reprodução

```bash
python tools/benchmark_pan_tk.py --library azimlib --output pan.json
python tools/benchmark_first_grab_tk.py --output first-grab.json
python tools/benchmark_pan_tk.py --library matplotlib --output mpl-pan.json
```

A terceira execução exige o ambiente de desenvolvimento com Matplotlib; ele não
é importado no primeiro modo nem pelo runtime. As implementações anteriores e
hashes estão em `tools/baselines/interactive-raster-before` e
`tools/baselines/interactive-tiles-before`; os relatórios anteriores permanecem
identificados como históricos, sem substituir seus hashes pelos atuais.

## Relação com o aceite atual

As tabelas acima preservam medições históricas dos snapshots indicados. “Atual” nessas tabelas significa o runtime daquele lote, não o kernel opcional posterior. O [aceite do passo 4](performance-acceptance.md) traz os hashes finais, base original mais detalhada, input humano/idle Tk e limites. Nenhum tempo antigo foi atribuído novamente ao runtime novo.
