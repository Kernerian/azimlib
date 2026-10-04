# Conferência integrada de layout — itens 2.08–2.10

Passo 2 aceito neste escopo: 624 testes/16.577 subtests passaram; 16 regressões
novas também passaram no wheel instalado. A versão permanece 0.1.0 alpha.

Os relatórios desse aceite preservam hashes dos módulos que os produziram;
Tk/Pillow/typography anteriores estão em `tools/baselines/interactive-tiles-before`.
As medições históricas não são relabeladas como execuções do viewer atual.
A suíte atual e galeria regenerada estão em [validação](validation.md); o
[aceite visual do passo 3](viewer-visible-acceptance.md) é evidência separada.

O lote combina mapas regionais, atlas vertical e grids aninhados com títulos
multilinhas, ticks a 35°, nomes dos eixos e rótulos globais. Legenda, barra de
escala, norte, rosa e overview são adicionados explicitamente pelo exemplo;
nenhum deles aparece por padrão.

`examples/layout_acceptance.py` mede 24 cenas: três composições, duas orientações
de colorbar, fontes de 14/18 pontos e 100/200 DPI. Gera seis conjuntos de
PNG/SVG/HTML com dados estaduais reais embarcados e rotas/valores sintéticos.
O cenário regional usa 4,6 × 5,8 polegadas; atlas e grid aninhado recebem espaço
compatível com os textos grandes. Os ticks são explicitamente mais esparsos
na fonte de 18 pontos: layout não altera uma FixedLocator para esconder colisões.

## Correções e evidências

- [Rotação](text-rotation.md): alinhamento do bloco após girar, modos editáveis,
  nome do eixo Y com anchor e título considerando caixas de ticks/descendentes.
- Padding da colorbar medido a partir dos textos major/minor reais, incluindo
  multilinhas e rotação. A [referência](layout-acceptance-reference.json) confere
  24 controles de labelpad e 18 distâncias físicas. Na posição superior, o label
  de Matplotlib usa baseline e deixa 4,64 pontos de vão no caso de oito pontos;
  Azimlib conserva os oito pontos até a caixa. Essa diferença é explícita.
- Barras compartilhadas usam a área de subplot efetivamente alocada na medição
  e reservam folga interna automática sem reescrever `bar.pad`. `cax` manual
  mantém sua posição. Falha de layout restaura posições e reservas anteriores.
- Overview pequeno acompanha a área real do mapa; a medição de layout não
  reprojeta a geometria do contexto. O foco permanece preto.
- [Matriz](layout-acceptance-matrix.json), `tests/test_layout_acceptance.py` e
  [54 composições](composition-matrix-reference.json). A fotografia anterior
  da matriz está em `tools/baselines/layout-acceptance-before/`.

O smoke `tools/smoke_layout_acceptance_tk.py` cobre seis cenários com edições,
toggles/restauração, resize a 200 DPI, foco/Home e comparação de RGBA/PNG/SVG.
Os [relatórios source](layout-acceptance-tk-source.json)/[wheel](layout-acceptance-tk-wheel.json)
registram 30 checks/18 frames cada, origem e hashes dos arquivos importados.
Nove scripts Tk anteriores passaram novamente no wheel, registrados em
[regressões](layout-acceptance-tk-regressions-wheel.json); o smoke de Artists
foi repetido separadamente source/wheel, com 14 checks cada.
Ele usa Tk real com janela oculta; não encerra o aceite de aparência/input da
janela visível do passo 3.08. A CI inclui esse smoke, mas execução remota e
outros sistemas não são evidências locais.

## Composição automática e manual

Layout reserva decorações de eixos, barras e rótulos globais; não é um solver
para qualquer par de textos. Textos livres, annotations, componentes sobre
dados, `add_axes()` e `cax` explícito exigem decisão do autor. `in_layout=False`
desenha o Artist sem reservar espaço. Posições globais explicitadas em
`fig.supxlabel(..., x=..., y=...)`/`supylabel(...)` são conservadas. Um setter de
posição em rótulo global ainda automático pode ter sua coordenada perpendicular
recalculada pelo engine, também observado diretamente no Matplotlib.

Grades não são obrigatórias. Dimensões insuficientes ou falta de convergência
geram aviso e conservam posições anteriores; fontes não são reduzidas
silenciosamente. Solvers próprios e rasterização não prometem os mesmos pixels
nem a mesma distribuição de espaço de todos os layouts Matplotlib.
