# Pan ao vivo e toolbar Tk

Outputs under `gallery/` are local generated previews, not distributed assets.
For versioned current images, see the [0.3 gallery](gallery-0.3.md).

O arrasto agora altera os limites durante o movimento e pede um redraw completo
no próximo idle do Tk. A composição permanece na thread da interface, mas a
rasterização roda em um worker próprio, sem chamar Tk, sobre primitivas
congeladas. Há uma vista ativa e somente a solicitação mais recente aguardando;
movimentos intermediários não formam uma fila crescente. Ticks, grade,
geometrias e componentes opcionais são
recalculados juntos. A moldura dos Axes não é arrastada como parte de um recorte
de imagem; o viewer não usa mais o preview de bitmap traduzido.

O início do arrasto guarda viewport, posição do cursor e limites originais.
Movimentos seguintes são calculados dessa mesma origem, inclusive quando houve
redraw entre eles. Soltar mantém o alvo do gesto e grava uma entrada no histórico;
Back/Forward/Home continuam restaurando a composição inteira. Views alteradas
pelo código antes de começar o gesto também entram no histórico.

Botão esquerdo desloca a vista; botão direito muda a escala projetada em torno
do cursor inicial. O gesto direito usa deslocamentos relativos às dimensões dos
Axes e escala base 10 com aspecto igual, em vez da sensibilidade fixa anterior.
X/Y restringem o gesto; Ctrl iguala os deltas cartesianos e Shift favorece eixo
ou diagonal. O domínio geográfico continua limitado, sem eixos invertidos ou
equivalência geral de projeções. A 0.3.0 em desenvolvimento acrescenta crossing
cilíndrico explícito: [ramo contínuo, histórico e navegação](geodesy.md). As
medições e comparações abaixo preservam o escopo do runtime que as produziu.

## Comparação direta e integração

[60 casos da referência instalada](pan-interaction-reference.json): TkAgg real
oculto, longitude/latitude com aspecto igual, dois botões, cinco modos de tecla,
duas âncoras e três deslocamentos. Os limites mudaram antes do release na
referência e coincidiram com a implementação própria; erro máximo aproximado
de 3,55 × 10⁻¹⁴ graus. Os testes consomem a fixture sem importar Matplotlib.
Isso compara contratos selecionados, não latência física ou todas as projeções.

[Source](pan-interaction-tk-source.json) e
[wheel instalado](pan-interaction-tk-wheel.json) conferem onze cenários: duas
atualizações durante o mesmo gesto, ticks deslocados, moldura fixa, igualdade
entre buffer exibido e Scene nova, release sem salto, uma entrada de histórico,
Home/Back/Forward, botão direito, responsividade e fechamento. Um renderer
deliberadamente bloqueado permite verificar que Tk continua processando um
temporizador e dez novos movimentos; o worker trabalha fora da thread da GUI.
Cinco testes do worker verificam ownership, fila limitada, erros e descarte
de resultados após invalidar/fechar. Codecs PNG são proibidos durante
o gesto testado. Os previews abaixo são buffers do nosso canvas; não são
screenshots da janela do sistema. Mais seis regressões cobrem simplificação,
cache de caminhos, coalescência antes da composição, holes/clipping e exportação.
Wheel zoom e seleção retangular também restauram pixels de qualidade completa.
Retornar sem botão pressionado encerra um gesto cujo release não chegou ao
canvas: mantém a última vista, limpa a seleção e não aplica o ponto de reentrada.
Retornar com botão pressionado continua o mesmo gesto. Há regressões para
ambos os botões, Enter/Motion, histórico e nova pegada; iniciar outro arrasto
descarta quadros atrasados do anterior. Isso evita restaurar uma vista obsoleta.
Uma regressão do poll garante que o início de um job aguardando não desative
o estado assíncrono e descarte o quadro final.

Local preview: Antes do pan (`gallery/pan-live-before.png`, generated locally)
Local preview: Enquanto o botão ainda está pressionado (`gallery/pan-live-during.png`, generated locally)
Local preview: Depois do release, mantendo a mesma vista (`gallery/pan-live-after.png`, generated locally)

## Toolbar

Os grupos seguem a referência Tk: Home/Back/Forward; Pan/Zoom/Subplots; Save.
As dicas aparecem imediatamente à direita do botão, alinhadas ao seu topo, e
desaparecem ao sair. Os ícones continuam originais da Azimlib; nomes permanentes
sob os ícones continuam opcionais. [Quatro escalas Tk](toolbar-reference.json)
comparam grupos, tamanhos, fontes, toggles e tooltip; o smoke próprio agora tem
28 checks por instalação, sem importar a referência.

## Reprodução

```bash
python tools/inspect_pan_interaction.py
python tools/smoke_pan_interaction_tk.py --output pan-check.json --previews previews
```

O primeiro comando é somente desenvolvimento no ambiente da referência. O
segundo funciona com `azimlib[gui]`. O redraw é completo e coalescido. Frames
intermediários completos podem ser exibidos enquanto o botão está pressionado;
após soltar ou mudar a vista, só o alvo atual é aceito. PhotoImage, cache,
widgets e callbacks continuam na thread principal. Fechar não espera pelo job
raster ativo; seus buffers são descartados quando ele termina.
`flush_events()` explícito processa eventos enquanto drena o frame solicitado,
com limite de 30 segundos; o mainloop normal não espera pelo worker.
Durante o arrasto e sequências de wheel, um processo de pixels separado usa
aggdraw genérico para preencher nossos polígonos de stroke antialiasados,
preservando a construção própria de dashes/caps/joins e even-odd. Texto continua
amostrado a 3x. Sem a dependência opcional há fallback para cobertura própria.
Caminhos longos são simplificados em espaço de tela com tolerância de 0,15 pixel;
um cache limitado reaproveita índices apenas após conferir todos os vértices
traduzidos. Zoom ou alteração de geometria exige simplificar novamente. O worker
ocupado permite uma Scene intermediária preparada enquanto o processo desenha;
demais movimentos guardam somente os limites mais recentes. Soltar, ou parar
o wheel por 120 ms, pede o raster exato. O cache de tiles e métricas/fontes,
primeira pegada e as limitações estão em [responsividade](pan-responsiveness.md).
Frames transitórios não entram no cache de imagens exatas. Textos, ticks,
legenda, grid e componentes usam a composição completa em ambos os caminhos.
`savefig()` não seleciona esse modo transitório. Veja as
[medidas reais de navegação](pan-responsiveness.md).

Cenas densas ainda podem gastar tempo em composição e raster, e isto não
promete igualdade de FPS com Agg. Os benchmarks antigos que incluem
`pan_preview_and_release` medem a implementação anterior e não representam a
latência deste novo pan. Medição de pintura/input visíveis continua em 4.09.
A conferência manual final de 3.08 permanece na
[checklist](viewer-visible-acceptance.md).
