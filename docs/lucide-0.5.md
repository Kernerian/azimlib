# Lucide: catálogo local e efeitos opcionais

Lucide1.61.0, commit c29c276f16590cf017126671535ad8c792be64d8;30 SVGs oficiais
sem alterações, hashes e aplicabilidade de Feather em assets/lucide/manifest.json.
O LICENSE upstream foi copiado verbatim para licenses/Lucide.txt: ISC e avisos
MIT de Cole Bemis para os ícones listados. O código original Azimlib continua BSD.
Não há dependência JS, rede ou aquisição durante import/render.

symbol_catalog()/lucide_catalog() expõem nomes oficiais; "lucide:bot" é Lucide,
"rover" é alias cartográfico documentado para bot, não um nome upstream.
"ivory"/"battle" conservam desenhos autorais quando não há alternativa adequada.
symbol_catalog("original") e "original:rover" preservam os18 desenhos anteriores.
Assets SVG/PNG/vetoriais do usuário continuam disponíveis na mesma API.

```python
import azimlib as a
f, ax = a.subplots(body=a.MARS)
ax.symbols([(0, 0)], "lucide:bot", size=20, color="#216d83",
           stroke_width=2, halo=a.IconHalo("white", width=0.7),
           shadow=a.IconShadow(alpha=0.2, offset=(0.7, 0.9), blur=0.8))
```

size/halo.width/offset/blur em pontos físicos; stroke_width em unidades do
viewBox original (24 para Lucide), independente do halo. Sem halo/sombra por
padrão. Scale opcional multiplica tamanho; limites de recursos mantidos.
Âncora e dados geográficos não mudam; picking exclui a decoração dos efeitos.
Traços/caps/junções arredondados e proporções preservados. SVG2 A/S/T e rects
arredondados agora são suportados com amostragem limitada própria das equações
W3C, sem copiar implementação externa. Segurança SVG anterior preservada.

Halo e sombra dura permanecem paths vetoriais em SVG/PDF. Blur>0 usa Pillow
opcional para apenas um pequeno tile RGBA da sombra (até1Mpx), incorporado com
alpha nos três backends. PNG customizado usa tiles locais para seus efeitos.
Nada desaparece silenciosamente e a página inteira nunca é rasterizada.
Sombras com blur não funcionam sem Pillow: erro explícito da dependência.

Prancha reproduzível: examples/thematic/lucide_050.py --output DIR.
Novas imagens exigem revisão humana; o aceite geral da Fase C anterior excluiu
o catálogo antigo e não é promovido a aceite destes novos ícones.
