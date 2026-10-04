# Limites dos contornos: checklist 1.09

O algoritmo continua próprio: marching squares sobre grid retangular crescente,
interpolação nas arestas, decider bilinear para saddles e união de segmentos.
Esta revisão fecha o subpasso **1.09** no conjunto existente; não acrescenta
contourf, corner_mask, grades irregulares ou um backend externo.

## Correção entregue

Um campo constante com níveis automáticos produzia valores repetidos e era
rejeitado. Agora cria um ContourSet vazio e editável, com um nível igual ao
valor constante. `allsegs` retorna `[[]]`, clabel retorna lista vazia e o handle
permanece ligado aos eixos; cor/largura/visibilidade/remoção e colorbar continuam
funcionais. O Matplotlib/Agg instalado também aceita campo constante, sem
linhas/rótulos, mas escolhe vários níveis muito próximos pelo seu locator.
Não copiamos aqueles pequenos intervalos numéricos: o locator automático da
Azimlib continua usando sua política documentada de espaçamento uniforme.

Quando o intervalo possui poucos floats representáveis, níveis automáticos
arredondados iguais são deduplicados. Quando o cálculo do intervalo/intermediário
transborda, é usada uma combinação convexa finita. O caso usual conserva a
aritmética e os níveis anteriores; isso não garante toda a geometria/normalização
de campos com magnitude extrema. Níveis explícitos não são deduplicados: precisam
continuar finitos, não vazios e estritamente crescentes.

## Regras auditadas e diferenças explícitas

| Situação | Azimlib | Referência instalada |
|---|---|---|
| Campo constante + níveis automáticos | Handle vazio editável, um nível; colorbar desenha | Handle vazio editável, níveis escolhidos por locator; colorbar desenha |
| Níveis fora do intervalo do campo | Grupos vazios, sem labels; estilos/mapping continuam editáveis | Mesmo contrato vazio nos casos registrados |
| Níveis repetidos/não finitos | Rejeição antes de anexar camada ou alterar vista | Rejeitados nos casos registrados |
| Lista explícita vazia | ValueError | Aceita ContourSet sem níveis; a colorbar do caso registrado falha com IndexError |
| Campo inteiro ausente | ValueError antes de anexar camada | Aceita ContourSet vazio com níveis explícitos |
| None/NaN/inf em célula | Exclui as células com qualquer canto ausente, sem cruzar a lacuna | Comparação feita com corner_mask=False; default do Matplotlib usa outro tratamento de cantos |
| Saddle bilinear | Determinante escolhe conectividade; empate exato usa pares (0,1)/(2,3) de arestas | Não prometemos mesma conectividade em empates degenerados |

As posições dos paths são unidas por coordenadas arredondadas a 12 casas;
limites de precisão/topologia extremamente pequenos continuam documentados.
clabel possui solver próprio e recorta somente sua linha conectada quando o
rótulo foi posicionado/está visível. Não recria curvas de nível por set_array:
esse setter edita valores de cor, conforme [o contrato](lines-contours.md).

## Verificação reproduzível

- [Referência](contour-boundaries-reference.json): dez casos produzidos pelo
  [tool](../tools/inspect_contour_boundaries.py) com Matplotlib 3.11.2/Agg instalado;
  aceita/rejeita, níveis, paths vazios, labels e possibilidade de desenhar colorbar.
- [Regressões](../tests/test_contour_boundaries.py): campos constantes, floats
  adjacentes/transbordamento, rejeição sem alterações, lacunas sem pontes,
  decider e norma compartilhada com scatter/colorbar.
- Integração em 100/200 DPI e colorbars vertical/horizontal: edição de cor/traço,
  atualização dos halos/cores dos labels, preservação de paths/vista manual,
  exportação PNG/SVG e remoção sem callbacks em figura antiga.

O teste utiliza os registros, sem importar Matplotlib em runtime. Esta entrega
não mede pintura de janela visível ou input físico e não fecha os demais aceites
da 0.2.0. A integração **1.10** e o aceite **1.12** foram posteriormente
encerrados no [passo 1](artist-acceptance.md); próximo item da lista: **2.08**.
