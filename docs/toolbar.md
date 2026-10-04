# Toolbar: contratos Tk e verificação visual

A auditoria do passo 3 encontrou e corrigiu diferenças na toolbar:

- Pan/Zoom agora são Checkbuttons sem indicador, com seleção sincronizada
  entre clique e atalhos, como a referência Tk do Matplotlib.
- Botões usam dimensões de 18 pontos; a barra pede a largura
  do canvas e mantém 50 pixels de altura.
- Hover plano/fundo neutro substituem
  o groove do Tk. Os sete ícones são **desenhos originais da Azimlib**, com
  geometria própria em src/azimlib/_toolbar_icons.py. Desktop gera RGBA direto
  com oito amostras por dimensão; HTML usa SVG da mesma geometria. Não há
  glyphs, caminhos ou imagens copiados da referência. Os assets próprios
  PNG 24/48 px e SVG são reproduzíveis por tools/build_toolbar_icons.py e
  seguem a licença BSD-3-Clause da Azimlib. [Auditoria](toolbar-icons-audit.json).
- Cursor de pan/zoom só aparece dentro do mapa; margens e saída do canvas
  restauram o cursor padrão.
- Subplots pertence ao grupo Pan/Zoom; Save fica após o segundo separador.
  Tooltips aparecem imediatamente à direita do botão, alinhados ao topo,
  como a referência Tk; não há atraso de 550 ms nem caixa abaixo do botão.
- [Pan ao vivo](pan-interaction.md) atualiza limites/ticks durante o movimento,
  usando origem congelada, e mantém a moldura fixa, sem preview de bitmap.

[Referência](toolbar-reference.json): widgets reais das duas bibliotecas em
96/120/144/192 DPI de escala Tk. Tipos, dimensões pedidas, fontes, hover e
sequência de seleção Pan/Zoom coincidem nos estados medidos; hover plano é
uma diferença de apresentação documentada. Isso usa Tk
8.6/Windows e Matplotlib 3.11.2 no ambiente separado de desenvolvimento.

![Ícones originais da Azimlib](../gallery/toolbar-icon-assets.png)

A imagem contém apenas os PhotoImages gerados pela Azimlib, **não é uma
screenshot de janela**. Os símbolos têm função/proporções familiares, mas
são construídos a partir de polígonos, elipses e retângulos definidos por nós.
Diferenças de tema/widget ainda requerem conferência visual. Matplotlib é
somente referência no ambiente separado de desenvolvimento.

Há quatro regressões sem janela/Matplotlib em tests/test_toolbar.py, três
regressões de limites/exportação em tests/test_subplot_editor.py, cinco
regressões próprias de assets/SVG/alpha/simetria e 28 checks
com Tk real e janelas ocultas em
[source](toolbar-tk-source.json)/[wheel](toolbar-tk-wheel.json). O smoke testa
widgets, estados, cursor nos handlers, nomes opcionais, editor e fechamento;
não entrada física.

## Nomes e editor Subplots

A toolbar padrão do Matplotlib mostra ícones com nomes/dicas no hover. A
Azimlib mantém esse padrão e oferece nomes permanentes opcionais:

```python
viewer = fig.show(block=False)
viewer.set_toolbar_labels(True)  # False restaura apenas os ícones
```

O editor foi reconstruído com widgets ttk e grupos Borders/Spacings, tomando
o diálogo Qt instalado como referência de organização. Sliders e campos
numéricos permitem edição ao vivo; limites relacionados preservam left < right
e bottom < top. Reset restaura uma cópia dos valores iniciais; Tight layout
recalcula a composição; Export values fornece código fig.subplots_adjust()
copiável. Um único diálogo é reutilizado e pode ser reaberto após fechar.
Layout automático incompatível desativa ajustes manuais, com explicação;
Tight layout permite mudar para o modo ajustável. O toolkit continua **Tk/ttk**,
sem exigir Qt no runtime. Não se promete que Tk reproduza a decoração nativa Qt.

## Reproduzir

Com `.[gui]` instalado:

```bash
python tools/smoke_toolbar_tk.py --output toolbar-check.json
python tools/show_viewer_comparison.py --library azimlib --labels --subplots
```

No ambiente separado com Matplotlib, execute:

```bash
python tools/inspect_toolbar.py
python tools/show_viewer_comparison.py --library matplotlib
python tools/show_viewer_comparison.py --library matplotlib --reference-backend QtAgg --subplots
```

Os comandos de comparação abrem uma janela **visível**, identificada e
posicionada lado a lado, com os mesmos dados/figsize/DPI e eixos de graus com
aspecto igual. Permite conferir canvas/margens, toolbar/hover, títulos/fontes,
cursor, Home/Back/Forward, pan/zoom e resize. Matplotlib só é importado quando
o modo `--library matplotlib` é selecionado; o viewer Azimlib não o utiliza.
QtAgg exige uma biblioteca Qt apenas no ambiente de referência; PySide6 foi
instalado nesse ambiente para permitir a comparação de desenvolvimento.

## Escopo da verificação

Comparação programática com a referência e observação visual Windows são
registradas em [viewer-visible-acceptance](viewer-visible-acceptance.md).
Linux/macOS têm testes Tk automatizados, sem avaliação visual nativa humana.
Os snapshots e resultados de desempenho permanecem históricos; não descrevem
automaticamente o runtime atual.
