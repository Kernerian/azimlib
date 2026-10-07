# Layout e margens automáticas

```python
import azimlib as azl

fig, ax = azl.subplots(figsize=(7, 6), layout="constrained")
ax.state("SP", facecolor="#eeeeee", linewidth=0.6)
ax.set_title("São Paulo\nFoco regional")
ax.set_xlabel("Longitude", labelpad=6)
ax.set_ylabel("Latitude", labelpad=6)
fig.savefig("estado.svg")
azl.show()
```

`azl` é apenas um alias Python. Também funciona `import azimlib.pyplot as plt`.
Matplotlib não é necessário para nenhuma dessas chamadas.

## Modos e unidades

| Chamada | Comportamento |
|---|---|
| `azl.subplots()` | Margens familiares fixas; nenhuma otimização automática |
| `fig.tight_layout(pad=1.08, w_pad=None, h_pad=None, rect=None)` | Mede e ajusta uma vez; deixa um engine inativo |
| `azl.subplots(layout="tight")` | Recalcula antes de cada desenho/exportação |
| `azl.subplots(layout="constrained")` | Recalcula com padding em polegadas; inclui suptitle e colorbars |
| `fig.set_layout_engine("none")` | Para o cálculo; preserva a política de ajuste do engine anterior |
| `fig.set_layout_engine(None)` | Remove completamente o engine; permite ajuste manual |

Em tight, pad/w_pad/h_pad são frações do tamanho de fonte global;
`rect=(left,bottom,right,top)`. Em constrained, w_pad/h_pad são polegadas
(padrão 3/72), wspace/hspace são proporcionais e
`rect=(left,bottom,width,height)`. `pad=0` é aceito, mas pode faltar folga para
diferenças de rasterização. `labelpad` dos rótulos X/Y usa pontos a partir
dos limites reais dos ticks, substituindo offsets fixos.
Rotação pública positiva é anti-horária, como no Matplotlib: `labelrotation=25`
inclina os números para cima à direita. A conversão para SVG/PNG, cujas
coordenadas têm Y para baixo, inverte o sinal internamente.

```python
fig.get_layout_engine().set(w_pad=0.06, h_pad=0.06)
fig.canvas.draw_idle()
fig.set_layout_engine(None)
fig.subplots_adjust(left=0.15, right=0.85, top=0.88, bottom=0.13)
```

Como na referência instalada, subplots_adjust avisa e não altera posições
quando constrained ou seu placeholder está ativo. Tight permite ajustes,
mas seu próximo desenho automático pode recalculá-los.

## Medição e componentes

O solver próprio usa as mesmas primitivas exportadas, com limites de glifos,
rotação, texto multilinha e bordas. Preserva a proporção da projeção; mapas
podem ocupar apenas parte do retângulo alocado, deixando espaço branco.
As medições não projetam novamente camadas de dados. A heurística de
`legend(loc="best")` pode, separadamente, analisar geometria para escolher posição.

No Tk, resize, mudanças de limites e edição de textos usam o engine no redraw.
PNG e SVG compartilham composição; mudar DPI preserva dimensões físicas.
HTML recebe o layout na exportação; não executa o solver Python ao navegar.

```python
legend = ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
legend.set_in_layout(False)  # continua visível, mas não reserva margem
legend.set_visible(False)   # deixa de ser desenhada
fig.canvas.draw_idle()
```

Títulos, rótulos, legendas, Axes e componentes oferecem set/get_in_layout.
`fig.suptitle/supxlabel/supylabel` reservam bordas da Figure conforme o engine;
suas posições/estilos são editáveis. Veja [rótulos globais](figure-labels.md).
Um Axes excluído mantém sua posição. Camadas são recortadas ao viewport e
não exigem margem externa. Layout não adiciona grid, escala, norte ou minimapa.
Colorbars compartilhadas entram na medição junto à união dos subplots.

`add_axes()` e `cax` explícito mantêm posições manuais. Na 0.3 em
desenvolvimento, textos livres e cax próximos das bordas podem reservar faixas
quando in_layout=True; objetos interiores continuam exigindo reserva manual.
Veja [contratos de composição](transforms-composition.md).

## Limites e verificação

Suporta hierarquias GridSpec com spans e pesos; veja
[composição com spans](gridspec.md) e [grids/mosaicos aninhados](nested-layout.md).
Na 0.3 em desenvolvimento, também aceita raízes independentes em regiões
explicitamente disjuntas, SubFigure e compressed em grids completos sem spans.
Hierarquias/spans mantêm a solução constrained. Não inclui alinhamento geral
de rótulos entre mapas com proporções diferentes nem colisão universal de textos. Não resolve colisões
internas entre legenda, escala, norte e dados. Até 16 medições em grids simples
ou 32 em hierarquias fazem reservas
conservadoras. Sem espaço/convergência, avisa e restaura posições anteriores;
aumente figsize ou reduza fontes/padding. Não reduz fontes silenciosamente.

O [exemplo](../examples/layout.py) gera atlas com colorbar compartilhada e legenda
externa. A [comparação visual](../gallery/layout-reference.png) usa os mesmos
dados/tamanho/estilos em Matplotlib/Agg e Azimlib/Pillow. layout-reference.json
verifica regras de engines e limites no canvas, sem declarar igualdade de pixels
ou equivalência completa dos solvers.

Referências: [tight layout](https://matplotlib.org/stable<local>/tight_layout_guide.html)
e [constrained layout](https://matplotlib.org/stable<local>/constrainedlayout_guide.html).
Matplotlib permanece somente no ambiente de desenvolvimento.
