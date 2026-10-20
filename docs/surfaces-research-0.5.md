# 0.5.0/3.05 — investigação de superfícies não oblatadas

Estado: investigação delimitada; **nenhuma geodésia triaxial ou irregular foi
implementada ou certificada**. A investigação não bloqueia as operações
esféricas/oblatadas demonstradas na Fase B. As recusas são testadas.

## Elipsoide triaxial

A conversão radial estática da Fase A permanece válida. Não se segue disso
que projeção inversa, latitude da normal, geodésica mínima ou área sejam
suportadas. Em particular não existe simetria de revolução para aplicar
Mercator/TM oblatas apenas trocando um raio.

Uma rota de pesquisa é a solução de Jacobi em coordenadas elipsoidais,
com tratamento próprio de umbilicais, polos de coordenadas e múltiplas
geodésicas. A documentação de referência
[GeographicLib triaxial](https://geographiclib.sourceforge.io/doc/triaxial.html)
discute métodos diretos/inversos; foi consultada como descrição científica,
sem incorporar código ou traduzir sua implementação. Não é dependência runtime.

Outra alternativa a investigar é integrar a equação de geodésica com restrição
`rᵀQr=1`, `Q=diag(1/a²,1/b²,1/c²)`. Para velocidade de comprimento unitário,
`r''=−(vᵀQv)/(rᵀQ²r) Qr`. O problema direto exige controle de erro e deriva
da restrição; o inverso exige busca de todas as soluções relevantes e decisão
da mínima, não apenas convergência de um shooting local. Essa formulação é
uma hipótese matemática de trabalho, não um solver entregue.

Área exige integral da métrica da parametrização da superfície, orientação,
furos/complementos e controle de erro. Planificação requer escolhas explícitas
de cortes e distorção. Uma imagem visualmente plana não demonstra conservação
de área, conformidade ou inversa global.

Antes de promover: corpus independente com eixos próximos/afastados,
umbilicais, antipodais, soluções múltiplas, conservação de comprimento/
restrição, área analítica quando disponível, domínio e orçamento congelados.

## Malha irregular

O SurfaceMesh atual valida triângulos e limites de memória; não certifica
variedade, fechamento, orientação global ou ausência de auto-interseção.
Essas propriedades precedem uma API de interseção radial/normal ou distância
de superfície. O menor caminho no grafo de arestas não equivale à geodésica
contínua sobre as faces.

Investigar métodos poliédricos com propagação de janelas/desdobramento e
aproximações declaradas, com distinção entre a superfície triangulada e o
corpo físico que ela aproxima. A descrição de
[geometria intrínseca](https://geometry-central.net/surface/intrinsic_triangulations/basics/)
é referência conceitual, não material incorporado. Parametrização de malha
requer cortes, múltiplas cartas, distorção e política para sobreposições;
não existe nesta fase uma planificação universal automaticamente invertível.

Antes de promover: testes de malha plana e superfícies desdobráveis com
solução conhecida, casos não convexos, componentes desconectados, fronteiras,
interseções múltiplas, singularidades, erro da discretização e memória limitada.

## Decisão arquitetural

BodySurface aceita somente esfera e elipsoide oblato no domínio do solver
existente (inverso do achatamento >=150). Triaxial/irregular recusam projeção,
geodésia, raster de superfície e iluminação geométrica desta fase; não recebem
fallback esférico. Coordenadas radiais triaxiais já entregues não são retiradas.
`Body.capability('irregular_geodesy')` permanece `research`.

Uma extensão futura deverá preservar Body/PlanetaryContext, medidas físicas,
ownership e Artists, mas fornecer solver/capability específico. Não se expõe
agora uma classe pública vazia de solver. Não há prazo ou certificação universal
prometidos, nem relação automática com o motor orbital 0.6.0.
