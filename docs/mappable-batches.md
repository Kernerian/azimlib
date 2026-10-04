# Edição agrupada de cores e dados

Layer, ScatterCollection, MeshCollection, ScalarImage e VectorCollection
aceitam `norm`, `cmap`, `clim` e `array` por `set()` e `azl.setp()`, combinados
com seus dados/estilos já editáveis. O núcleo e o desenho continuam próprios.

```python
import azimlib as azl
from azimlib.colors import Normalize

fig, ax = azl.subplots()
image = ax.imshow([[1, 2], [3, 4]], extent=(-54, -44, -26, -18))
bar = fig.colorbar(image, orientation='horizontal')

image.set(data=[[10, 20, 30]], norm=Normalize(),
          cmap='plasma', clim=(0, 50), alpha=.8)
fig.savefig('campo.svg')
```

## Contrato dos lotes

- `norm` exige Normalize próprio ou sua subclasse; `None` cria Normalize novo.
- `cmap` usa nome/paleta própria ou Colormap; `None` retorna à paleta padrão
  viridis. A atribuição `item.cmap = 'plasma'` agora valida e notifica a mudança,
  como `set_cmap`. Não há rcParam `image.cmap` nesta etapa.
- `clim=(vmin,vmax)` muda os limites. `None` em uma extremidade preserva seu
  limite existente; um escalar é o limite inferior, como em `set_clim`.
- O lote considera os dados e a norm finais, independentemente da ordem dos
  argumentos. Limites explícitos completos prevalecem; limites não definidos
  podem ser preenchidos pelos dados novos. Limites previamente fixados continuam
  fixos, até edição explícita ou `autoscale()`.
- `array` segue a forma/quantidade aceita pelo handle. ScalarImage mantém sua
  ordem geográfica legada para vetor plano; prefira `data` para matriz na ordem
  original. `data` e `array` juntos são rejeitados na imagem. Veja [campos](field-editing.md).

Offsets/sizes, extent/forma da imagem, UVC/scale e estilos também podem entrar
no mesmo lote. Dados e propriedades são verificados antes de alterar o handle
ou a norm compartilhada. Erros comuns de forma, paleta, intervalo ou estilo
preservam dados, cores, visibilidade e callbacks. A validação prospectiva usa
uma cópia rasa da norm com callbacks isolados, sem mudar a instância original.

## Observadores e colorbars

Um lote em um handle agrupa suas notificações de Artist e de ScalarMappable;
os observadores recebem os dados/estilos/cores finais. Uma norm compartilhada
continua notificando os outros mappables quando seus limites mudam. Não há
transação entre vários Artists, rollback de callbacks que lançam exceções ou
garantia de isolamento para efeitos externos de subclasses customizadas de norm.
Matplotlib aplica seus setters em sequência; o agrupamento/validação prévia é
uma garantia própria da Azimlib, sem prometer contagem idêntica de sinais.

Alterar a paleta ou clim com a mesma norm preserva locators/formatters
personalizados da colorbar. Substituir a instância de norm redefine seus
tickers, como Matplotlib; a conexão com a norm antiga é removida.
Setters individuais, `getp`, SVG/PNG e exportação HTML usam os mesmos handles.
Editar cores/dados não muda automaticamente o extent geográfico.

## Comparação e limites

[mappable-batches-reference.json](mappable-batches-reference.json) registra 20
estados de Matplotlib 3.11.2/Agg: imagem, mesh, pontos e vetores, antes/depois
do lote, troca de norm, atribuição de paleta e retorno à paleta padrão.
O tool `inspect_mappable_batches.py` importa Matplotlib somente em desenvolvimento;
os testes da Azimlib usam o JSON e não precisam dele.

As regressões adicionais cobrem callbacks finais, norm compartilhada, inválidos
sem alteração parcial, 24 ordens de argumentos, dados/geografia no lote, missing
values, norm logarítmica/divergente/discreta, exportações e igualdade PNG entre
lote e setters dedicados. Não entregamos aqui edição completa de contornos,
reclassificação/regeneração automática de legendas temáticas ou RGBA/máscaras.

Veja o [exemplo](../examples/mappable_batches.py),
[antes](../gallery/mapping-before.png) e [depois](../gallery/mapping-after.png).
