# Auditoria de validação e integração de Artists 2D

Este lote consolida o primeiro critério da 0.2.0 sem incluir um backend externo.
O conjunto auditado cobre linhas, scatter, campos raster/mesh/vetores, contornos,
textos/annotations, spines, outline de colorbar, frame de legenda, escala e ticks.

## Correções entregues

- Propriedades numéricas de estilo são validadas e armazenadas como floats.
  Strings numéricas aceitas não deixam valores incompatíveis com a composição.
- Família/tipo/peso de fonte inválidos falham antes de editar dados, controles,
  estilos, norm, colorbar ou notificações. O suporte atual de fontfamily é uma
  string; fontstyle é normal/italic/oblique e fontweight normal/bold ou 100–900.
- Fontsize/labelsize devem ser positivos na Azimlib. Matplotlib pode converter
  tamanhos não positivos em um mínimo: esse detalhe não é reproduzido. Ocultar
  texto continua sendo feito com set_visible ou os controles de ticks.
- Padrões personalizados de tracejado são copiados para tuplas imutáveis.
  Geradores são consumidos uma única vez; editar a lista de entrada não muda
  a linha ou os contornos existentes. Não implementa offset+sequência Matplotlib.
- Spine/outline e LegendFrame validam o lote antes de editar o estado.
  Por exemplo, cor válida com linewidth inválido não deixa uma cor parcial.
- ScaleBar valida também sua criação. Uma tentativa inválida não substitui
  o componente anterior. Criação/edição usam a mesma validação de dimensões.
- tick_params normaliza tamanhos numéricos antes de atualizar configurações;
  labelsize inválido não modifica os labels nem as opções dos ticks/colorbar.

As validações não constituem rollback geral de callbacks, vários Artists,
normalizadores customizados ou edição direta de dicionários. Este lote não
acrescenta um parser completo de cores/fontes ou máscaras de dados.

## Evidências

- [Regressões](../tests/test_artist_validation.py): 12 testes/52 subtests
  adicionais; estado da figura, ownership, notificações, mappables compartilhados,
  dados/estilos e exportação após sucesso/falha.
- [Referência direta](artist-validation-reference.json): estados selecionados
  de setters e rejeição de fontes em Matplotlib instalado. A referência só é
  executada no desenvolvimento; o teste usa o registro sem importar Matplotlib.
- [Exemplo](../examples/artist_validation.py): rotas e valores sintéticos,
  antes/depois em PNG/SVG/HTML, com norm compartilhada, legenda, escala e contornos.
- [Smoke Tk](../tools/smoke_artist_validation_tk.py): sete verificações em
  janela real oculta. Um lote de edições gera um redesenho; seis falhas preservam
  imagem, SVG/modelo e contagem de draws. Não mede input físico, aparência nativa,
  latência ou bases densas reais.
- Relatórios [source](artist-validation-tk.json) e
  [wheel instalado](artist-validation-tk-wheel.json).

## Integração com o corte

Validação de propriedades numéricas/fontes/tracejados e edição de bordas do
conjunto acima está entregue. Propriedades/aliases, contornos e integração das
camadas foram consolidados no [aceite do passo 1](artist-acceptance.md).
Bases originais mais detalhadas e pintura/input físicos permanecem nos passos
4–5 da checklist. Não significa que
toda a API Artist/Line2D/Patch/Collection/Transforms do Matplotlib exista.
