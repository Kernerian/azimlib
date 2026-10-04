# Visibilidade, substituição e ciclo de vida de componentes

O protocolo próprio de Artist continua preservando handles editáveis, stale,
callbacks e o caminho separado de exportação estática/viewer. Este lote corrige
referências descartadas e o momento de registrar uma nova colorbar, sem usar
Matplotlib no runtime.

## Ocultar um componente ou seu texto

```python
legend = ax.legend(title='Camadas')
legend.set_visible(False)                 # Oculta a legenda inteira.
legend.set_visible(True)
legend.get_title().set_visible(False)     # Oculta somente o título.
legend.get_texts()[0].set_visible(False)   # Oculta o texto, preservando o símbolo.

bar = fig.colorbar(points, ax=ax, orientation='horizontal')
bar.label_artist.set_visible(False)       # Oculta somente o rótulo da barra.
```

Títulos de legenda, textos de entradas, ticks e rótulos de colorbar são filhos
estruturais. Seu `remove()` agora levanta `NotImplementedError` antes de alterar
visibilidade/stale, em vez de falhar com IndexError ao tratar os textos da
legenda como tuplas da Figure. Use `set_visible(False)`. Textos livres da
Figure, títulos/rótulos de MapAxes e camadas com remoção implementada continuam
removíveis. `set_visible(True)` não reinsere um Artist já retirado da composição.

## Substituir e limpar

Escala, norte, rosa, overview e colorbar local têm slots independentes nos Axes.
Uma nova instância válida do mesmo tipo substitui a anterior e desconecta seus
handles. Um argumento inválido preserva a instância atual. Norte e rosa
continuam coexistindo; não substituem um ao outro.

```python
previous = ax.scale_bar(length=200)
scale = ax.scale_bar(length=100)
assert previous.get_figure() is None

old_bar = ax.colorbar(mapping)
bar = ax.colorbar(mapping, orientation='horizontal')
assert old_bar.get_figure() is None
```

Colorbars locais antigas desconectam o callback do mappable na substituição ou
em `ax.clear()`. Colorbars compartilhadas e as de `cax` explícito são Artists
da Figure e não são removidas ao limpar apenas um mapa; podem ser retiradas
por `bar.remove()` ou `fig.clear()`. Alterar um mappable que ainda seja uma
camada ativa continua invalidando seus Axes, mesmo se sua barra foi removida.

A construção de uma colorbar não agenda desenho antes do registro. Em `ion()`,
adicionar/substituir a barra local ou limpar os Axes solicita uma atualização
com o estado final. Não há transação com rollback geral entre vários Artists.

## Rótulos de ticks descartados

Trocar ticks/locator/formatter descarta os textos explícitos correspondentes,
desconectando owner/parent antigos; eixos compartilhados seguem a mesma regra
ao sincronizar ou entrar no grupo. A substituição de norm de colorbar também
descarta ticks maiores/menores antigos. Alterar apenas clim ou mudar orientação
preserva os handles explícitos atuais.

```python
old = ax.set_xticks([-50], ['Antigo'])
current = ax.set_xticks([-45], ['Atual'])
assert old[0].get_figure() is None
current[0].set_color('red')
```

Editar os handles descartados não invalida a Figure anterior. Consulte os
handles retornados pelo setter atual; a reutilização completa de objetos Tick
do Matplotlib não está implementada.

## Referência direta e limites

[Registro local](component-lifecycle-reference.json): Matplotlib 3.11.2/Agg e
Azimlib, nove contratos observados. Cinco coincidem: remoção não suportada de
texto de entrada, visibilidade independente de entrada/título/frame, rótulo de
colorbar ocultável, locator preservado ao mudar clim e reiniciado ao trocar norm.

Quatro diferenças são explícitas: Matplotlib retém/reutiliza ticks antigos;
sua barra ocupa outro Axes e sobrevive ao clear do mapa; remover uma legenda
antiga limpa a referência à atual no caso registrado; editar o mappable de uma
barra removida ainda marcou a Figure como stale nesse experimento. Azimlib
desconecta ticks descartados, remove sua barra local com o mapa e preserva a
legenda atual quando uma anterior é removida. O caso de mappable independente
de barra removida permanece limpo. Esses resultados são do experimento, não
uma afirmação sobre todos os backends ou versões da referência.

Doze regressões adicionais/18 subtests verificam integração da Scene/SVG,
visibilidade reversível, callbacks, eixos compartilhados, validação antes de
substituir e desenho observando o registro completo. O [smoke Tk](../tools/smoke_component_lifecycle_tk.py)
confere sete cenários em janelas reais ocultas com edições programáticas;
não mede input físico, pintura visível ou latência. O lote seguinte corrigiu
o primeiro draw: callbacks e canvas são registrados antes dele, com recuperação
de erro e fechamento reentrante. Veja [integração de composição](sizing-composition.md).

O [exemplo](../examples/component_lifecycle.py) gera
[antes](../gallery/component-lifecycle-before.png) e
[depois](../gallery/component-lifecycle-after.png), com PNG/SVG estáticos e
HTML separado. Todos os componentes são adicionados explicitamente.

```bash
python examples/component_lifecycle.py
python tools/smoke_component_lifecycle_tk.py
# Somente desenvolvimento, requer Matplotlib:
python tools/inspect_component_lifecycle.py
```

Ainda faltam ampliar propriedades e casos de integração dos Artists existentes,
conferir composição em outros tamanhos/DPI, input/aparência nativos e resultados
reais de CI. Não se declara fechado o critério de Artists da [0.2.0](release-0.2.md).

Múltiplos grupos/matrizes, ciclos e defaults de legenda em contextos foram
consolidados no [lote de séries e estilos](series-styles.md).
