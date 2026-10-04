# Edição dos campos 2D

MeshCollection, ScalarImage e VectorCollection são handles próprios derivados
de Layer/Artist. O renderer continua recebendo somente primitivas de cena;
Matplotlib não participa da leitura, projeção, composição ou desenho.

```python
import azimlib as azl
from azimlib.colors import Normalize

fig, ax = azl.subplots()
image = ax.imshow([[0, 1], [2, 3]], extent=(-50, -40, -20, -10),
                  origin='lower', norm=Normalize(0, 10))
bar = fig.colorbar(image)
image.set_data([[2, 4, 6]])
image.set_extent((-55, -40, -25, -15))
image.autoscale()  # Atualiza explicitamente o intervalo de cores.
fig.savefig('campo.svg')
```

## Imagens escalares

`ScalarImage.set_data(Z)` aceita matriz retangular escalar não vazia; a forma
pode mudar. As bordas das células são recalculadas no mesmo extent geográfico.
`get_data()` devolve cópia na ordem original da matriz. origin='upper' mantém
a primeira linha ao norte; lower a mantém ao sul. RGB/RGBA e arrays mascarados
de NumPy ainda não têm contrato próprio.

`get_extent()` e `set_extent((west,east,south,north))` controlam a geografia da
imagem. São exigidos limites finitos, crescentes e dentro de ±180°/±90°.
`image.set(data=Z, extent=..., alpha=.5)` e setp editam esses campos num lote.
Dados/extent inválidos e estilos rejeitados são verificados antes da alteração.

Para preservar a API inicial da Azimlib, `get_array()` continua retornando um
vetor plano em ordem geográfica sul→norte. `set_array(flat)` mantém a forma
existente e usa essa ordem; `set_array(matrix)` equivale a set_data. Isto difere
do get_array de AxesImage, que retorna uma matriz. Use get_data/set_data no
código novo para evitar ambiguidade de origin. Uma imagem não aceita array=None.

## Malhas de células

`pcolormesh` retorna MeshCollection. `set_array(Z)` aceita matriz com forma
`(len(lat)-1,len(lon)-1)` ou vetor plano de mesmo total. As bordas permanecem
fixas. `get_array()` é plano; `get_coordinates()` retorna cópia da grade de
pares longitude/latitude das bordas. Sem NumPy, essas consultas usam listas.
`mesh.set(array=Z, visible=True)` também funciona.

`mesh.set_array(None)` suspende o desenho das células, preservando sua geometria;
não é um preenchimento automático com facecolors previamente calculados.
None/NaN/infinito em células são lacunas. Não há resampling ou rasterização
georreferenciada implícita: cada célula continua um quadrilátero projetado.

## Vetores

```python
vectors = ax.quiver([-52, -48], [-25, -21], [1, 0], [0, 1], C=[20, 80])
vectors.set_UVC([0, 2], [2, 0], [30, 90])
vectors.set_offsets([[-54, -28], [-43, -18]])
vectors.set_scale(20)
```

VectorCollection.set_UVC(U,V,C=None) atualiza as componentes leste/norte e,
se fornecidas, as cores numéricas. C omitido/None mantém as cores existentes,
como Quiver; `set_array(None)` retira o mapeamento de cores. Componentes e C
escalares ou sequências de um elemento expandem para todas as origens. Na
Azimlib são armazenadas as componentes efetivas por origem; os caches internos
de Quiver podem conservar arrays de um elemento.

`get_UVC()` é uma conveniência própria que retorna cópias de U, V e C. Offsets
são longitude/latitude; a quantidade de vetores é fixa. `set_offsets()` move as
origens; `set_scale(None)` retorna ao cálculo automático de escala. scale é
positivo e representa unidades dos dados por largura do Axes. U/V devem ser
finitos; máscaras de vetores ainda não são suportadas.

`vectors.set(UVC=(U,V,C), offsets=..., scale=...)`/setp agrupa a edição. Um
array explícito separado precisa de um valor por origem; combinar esse array
com C dentro de UVC é rejeitado. Formas/valores inválidos não deixam alterações
parciais nos dados, estilos ou visibilidade.

## Vista, callbacks e limites

Os mesmos handles preservam norm, paleta, colorbar e callbacks. Atualizar valores
não redefine limites de cores já fixados: use autoscale ou set_clim. Norm
compartilhada continua atualizando todos os campos associados. Validação de
intervalos prospectivos evita alterar dados antes de descobrir limites invertidos.

Edição de dados/origens/extent não muda a vista automaticamente. Depois de
alterar a geografia, `ax.relim(); ax.autoscale_view()` ajusta somente eixos
automáticos. Esta é uma política explícita da Azimlib; imshow inicial respeita
limites manuais de cada eixo e fixa por extent os eixos ainda automáticos.
Edições de extent não copiam todas as regras de sticky_edges
de Matplotlib. Valores de imagem e direção de vetor não alteram a geografia
dos limites. Veja [normalização e limites](norm-limits.md).
Os casos de limites manuais foram comparados diretamente à referência no
[aceite de integração](artist-acceptance.md).

set/setp aceita norm/cmap/clim junto dos dados/estilos e agrupa notificações do
mesmo handle. Veja [lotes de cores](mappable-batches.md). Não há transação geral
entre diferentes Artists, callbacks ou normalizadores externos. Setters dedicados
continuam disponíveis. remove/clear desligam os handles da figura. O HTML continua uma
exportação; alterações posteriores em Python exigem nova exportação.

O [exemplo antes/depois](../examples/field_editing.py) usa dados sintéticos.
[field-edits-reference.json](field-edits-reference.json) compara oito estados
de imagem, dois de mesh e quatro de vetores efetivos com Matplotlib 3.11.2/Agg.
Contornos e clabel têm [handles de estilo/texto editáveis](lines-contours.md),
mas sua geometria não é recalculada implicitamente ao editar outro campo;
animação, blitting, RGB/máscaras e novas coordenadas de mesh continuam pendentes.
