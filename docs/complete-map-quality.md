# Mapas completos em vários DPI

São Paulo, Brasil e atlas foram comparados em 100, 150 e 200 DPI, com as
mesmas geometrias de tela, fontes DejaVu, cores, espessuras físicas, clipping
e componentes opcionais. Os dados são os já distribuídos com a Azimlib;
os valores temáticos do atlas são sintéticos.

O renderer próprio produz o PNG/SVG final. Uma ferramenta **somente de
desenvolvimento** envia a mesma Scene cartográfica para Matplotlib 3.11.2/Agg
e gera comparações lado a lado e diferenças de pixels. Isso isola rasterização:
não compara o layout de Axes do Matplotlib, seus locators, algoritmos geográficos
ou GUI. As referências diretas de layout/API continuam nas comparações específicas.
Matplotlib não entra no runtime ou wheel da Azimlib.

O adaptador trata alpha global depois de fill/stroke, clip retangular, curvas
de círculos, traços, alinhamento/rotação de textos, fontes explícitas e buracos
simples aninhados. Agg usa fill nonzero: as orientações dos anéis simples são
convertidas no adaptador para conservar a paridade. Caminhos auto-intersectantes
complexos não estão cobertos por essa conversão. O halo de texto usa contorno
vetorial sob o preenchimento hinted; também não é um oracle perfeito para halo.

## Diagnóstico

O relatório [map-quality.json](map-quality.json) registra nove pares, dimensões,
hashes, métricas e arquivos. A diferença absoluta média de RGB usa valores
0–255. A média sobre pixels ocupados exclui pixels quase brancos dos dois lados;
evita esconder diferenças num canvas com muita margem. Essas métricas são
diagnósticos descritivos, sem limiar de aprovação perceptual ou promessa de
igualdade de pixels. Tempos observados no adaptador não são um benchmark
comparável de duas bibliotecas completas.

Há diferenças visíveis de hinting, antialiasing e posição subpixel de glifos,
bordas e linhas. O renderer próprio preserva suas fontes, cobertura e
supersampling. Os pares não são idênticos, e os nove casos não encerram o
critério de qualidade da 0.2.0. A conferência de SVG em todos os viewers/DPI,
mais estilos/recortes e comparações de layout independentes continuam necessárias.

| Caso | DPI | RGB médio absoluto | RGB nos pixels ocupados | Pixels com diferença máxima >16 |
|---|---:|---:|---:|---:|
| state | 100 | 1.796 | 2.840 | 2.03% |
| state | 150 | 1.720 | 2.744 | 1.54% |
| state | 200 | 1.752 | 2.815 | 1.36% |
| brazil | 100 | 2.495 | 11.633 | 3.32% |
| brazil | 150 | 1.421 | 7.177 | 2.06% |
| brazil | 200 | 1.657 | 8.642 | 1.73% |
| atlas | 100 | 2.670 | 4.597 | 2.64% |
| atlas | 150 | 1.880 | 3.271 | 1.72% |
| atlas | 200 | 2.227 | 3.886 | 1.55% |

## Reproduzir

No ambiente de referência de desenvolvimento com Matplotlib, NumPy e Pillow,
instale a Azimlib local e execute na pasta do projeto:

```bash
python tools/compare_map_quality.py --cases state brazil atlas --dpi 100 150 200
```

A ferramenta escreve PNG próprio, PNG Agg, comparação, diferença e SVG em
`gallery`. Pode selecionar `--gallery` e `--output`. Dados e fontes permanecem
locais; não há downloads implícitos. O projeto continua independente dessas
dependências de referência em sua execução normal.

Veja também [a otimização de clipping e a memória medida](performance.md).
