# Qualidade das imagens e comparação com Matplotlib

O PNG da Azimlib ainda pode parecer menos refinado que o Matplotlib/Agg.
Os renderizadores têm algoritmos diferentes. Nossa implementação constrói
os traços e máscaras, usa cobertura fracionária para linhas e rasteriza em
resolução ampliada antes de reduzir por média de área. Pillow fornece os
buffers e a rasterização das fontes. Agg tem tratamento refinado de curvas,
junções, antialiasing e alinhamento de elementos na grade de pixels.

Os testes de espessura mostram bom acordo de **área de tinta** em segmentos
retos; isso não prova igualdade pixel a pixel para curvas, texto ou símbolos.
DejaVu e unidades físicas são compartilhadas entre os caminhos PNG/SVG, mas
hinting, cobertura das bordas, caps/joins e arredondamentos ainda podem diferir.

Uma comparação justa exige mesmo figsize, DPI, fonte, linewidth, cores,
dados e escala de exibição. A imagem na tela pode ser redimensionada pelo
viewer ou navegador. Compare também os arquivos em tamanho original.

## Correção dos preenchimentos

Foi detectado um engrossamento independente do DPI: o preenchimento inteiro
incluía pixels extras na borda. O preenchimento agora usa scan conversion
próprio, intervalos even-odd entre arestas ativas, interseção horizontal
fracionária e integração vertical em estratos, subdivididos nos vértices.
Isso respeita buracos, concavidade e anéis sobrepostos sem XOR de máscaras
que já perderam informação subpixel. A saída mantém supersampling 3×.

Na bateria a 100 DPI, o círculo de raio 2,5 pixels passou de +8,67% para
−0,18% de erro de área. Um retângulo estreito de 0,8×12,7 pixels passou de
+70,60% para −0,03%. Não são métricas de similaridade de toda a imagem.
Dados completos em fill-validation-before.json e fill-validation-after.json.
Regressões usam área geométrica analítica, paridade, vários DPIs e alpha.

As caixas de fundo e colisão dos textos usam o mesmo cálculo tipográfico
no PNG/SVG, incluindo alinhamento e rotação. Textos com halo ou fontes fora
das variantes distribuídas ainda exigem comparação específica.

Colorbars e pcolormesh usam preenchimentos sem antialiasing individual nas
fronteiras entre células para evitar frestas. pcolormesh aceita
`antialiased=False` (padrão); `True` ativa cobertura fracionária por célula,
podendo expor seams em fronteiras compartilhadas. Essa escolha corresponde
ao papel de antialiased em malhas; a rasterização final ainda é supersampled.

```python
fig.savefig('mapa.png', dpi=200)  # mais pixels para o mesmo tamanho físico
fig.savefig('mapa.svg')          # vetorial, fontes usadas embutidas
```

Aumentar o DPI ajuda na rasterização, mas não corrige layout, desenho de
componentes nem dados excessivamente simplificados. SVG preserva a resolução
ao ampliar; não torna a geometria ou a tipografia automaticamente idênticas.
Mapas Natural Earth generalizados continuarão com menos detalhe que uma base
de alta resolução, independentemente do formato.

Próximas medições devem separar diferenças de geometria, layout, texto e
cobertura de pixels: curvas em vários ângulos, junções/caps, marcadores,
hachuras, alfa e glifos, sempre com DPI/fontes iguais. O ganho de desempenho
por tiles locais preserva o algoritmo de desenho existente; não equivale a
uma alegação de qualidade visual já igual ao Agg.

Referência: [backends e renderizadores do Matplotlib](https://matplotlib.org/stable<local>/backends.html).
