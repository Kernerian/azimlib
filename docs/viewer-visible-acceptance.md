# Verificação visual e funcional do viewer

Referência técnica do viewer Windows em 2026-10-03. A observação visual e os
testes programáticos são evidências diferentes; não houve captura automatizada
da janela. Este registro não valida a aparência nativa de Linux/macOS.

## Controles e contratos

- Título Figure, canvas, margens e área branca coerentes com a referência.
- Sete ícones próprios, tooltips legíveis, Pan/Zoom exclusivos e seleção visível.
- Coordenadas dentro dos Axes; fora deles o indicador é limpo.
- Pan e zoom retangular; Home restaura a vista e Back/Forward percorrem o histórico.
- Resize mantém canvas, toolbar e textos utilizáveis.
- Subplots edita margens, oferece Reset, Tight layout e Export values.
- Salvar exporta PNG/SVG estático; cancelar não cria um arquivo.
- Ornamentos permanecem opcionais; fechamento não deixa diálogos órfãos.

## Correções e limites

Subplots pertence ao grupo Pan/Zoom. Tooltips aparecem à direita do controle.
Ticks e limites acompanham o pan, mantendo a moldura do mapa fixa. O renderer
temporário preserva a espessura; o release restaura a qualidade final. Gestos
com release perdido terminam na última posição pressionada e frames antigos
são invalidados para evitar saltos ao sair e retornar ao canvas.

[Contratos e comparação](pan-interaction.md), [medições](pan-responsiveness.md)
e [diferenças](visual-differences.md) conservam dados técnicos e limitações.
Onze checks Tk source/wheel cobrem bordas/navegação; seis casos verificam
coordenadas contra a Scene completa. O snapshot histórico é
`tools/baselines/viewer-accepted-3-08`. A observação visual não é medição de
latência física nem equivalência de FPS. Os critérios 3.08–3.10 cobrem o escopo
da [checklist](release-progress.md), não toda a API Matplotlib.

Ícones, raster, métricas e Tk/ttk são próprios ou separadamente licenciados.
Zoom pela roda é uma conveniência; nomes permanentes são opcionais por
`viewer.set_toolbar_labels(True)`. Não se promete aparência Qt ou pixels iguais.
