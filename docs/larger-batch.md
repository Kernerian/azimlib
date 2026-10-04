# Consolidação de aliases, composição e navegação

Lote de 2026-10-02 para a fundação 0.2.0. A versão continua 0.1.0 alpha.

## Propriedades de Artists

Aliases explícitos são normalizados antes dos defaults internos. `lw`, `ls`,
`fc`, `ec`, `ms`, aliases de marcadores e aliases de texto continuam aceitos.
`linewidth=1, lw=1` agora gera TypeError, mesmo com valores iguais: não há
escolha silenciosa de uma das duas grafias. A falha ocorre antes de anexar
camadas, alterar limites/ciclo, texto, visibilidade ou callbacks dos Artists
auditados. Edições de grid com `lw`/`c` substituem o estilo anterior.

O contrato selecionado de 13 pares de aliases foi registrado diretamente no
Matplotlib instalado por `tools/inspect_style_aliases.py`, em
`style-alias-reference.json`. Azimlib mantém ha/va como nomes internos; isso
não muda as grafias públicas. Não se promete toda a API de propriedades.
`fontdict` e kwargs de set_title são camadas distintas: o kwarg prevalece.

## Composição

`examples/composition_components.py` combina duas áreas, títulos multilinha,
Latitude/Longitude com labelpad, dados sintéticos, losangos, legenda, escala,
norte, rosa dos ventos e overview de foco preto. Uma colorbar compartilhada
tem versões horizontal e vertical. A grade aparece somente no mapa que a pede.

Doze combinações de dois tamanhos, 72/100/180 DPI e duas orientações verificam
contenção dos textos, viewports positivos e foco do overview. Regressões
adicionais verificam escala física do desenho, visibilidade de cada componente,
norm compartilhada, posições explícitas e separação PNG/SVG/HTML.

Matplotlib também reposiciona suptitle automático depois de set_position()
quando constrained layout está ativo. Azimlib preserva essa regra. Para uma
posição manual persistente, use a chamada pública com coordenadas explícitas:

```python
fig.suptitle('Título', x=0.47, y=0.97)
```

## Cache de raster no viewer

Cada janela Tk mantém uma LRU de até quatro frames e 16 MiB de pixels RGBA
retidos. O limite não inclui a imagem ativa, PhotoImage, cenas, objetos Python
ou cópias temporárias. Frames grandes demais continuam pela renderização direta.
Fechar a janela libera o cache. Falhas de alocação opcionais também retornam
à renderização direta.

O hash SHA-256 usa os elementos desenhados completos: dimensões, fundo,
geometria, ordem, estilos, textos, recortes e conteúdo das fontes empacotadas.
Não arredonda coordenadas. Cada hit devolve uma cópia própria; modificá-la não
corrompe o cache. A cena e metadata de navegação são recompostas em cada draw,
que conserva draw_event. Alterações visuais/DPI geram outro frame. O cache é
exclusivo de show() Tk: savefig() continua rasterizando o conteúdo estático.

Oito verificações em Tk real, com janela oculta, foram executadas tanto no
source quanto no wheel instalado sem Matplotlib/GIS. Conferem pixels iguais
ao raster direto/PNG, histórico, edições, limite, fallback e cleanup:
`raster-cache-tk-source.json` e `raster-cache-tk-wheel.json`.

## Base municipal real e limites de desempenho

Download de desenvolvimento: malha de São Paulo subdividida em municípios,
fornecida pela [API oficial do IBGE](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3).
A própria documentação descreve as malhas da API como simplificadas; qualidade
maxima não significa a malha original em resolução integral. Foram lidos 645
features, 222.324 posições e 4.913.339 bytes. A proveniência e o SHA-256 estão
em `real-geojson-provenance.json`. O GeoJSON fica em work/bench-data, fora dos
artefatos distribuídos. Não há download implícito nem afirmação de licença.

`tools/benchmark_real_geojson.py` aceita um arquivo local de qualquer origem.
A leitura/validação usa o núcleo próprio. Estado inteiro, foco regional, pan
e zoom tiveram cenas e PNGs idênticos com índice ou varredura linear, em três
pares alternados por vista. Os relatórios conservam amostras e memória de
processo, medida fora do tempo da operação.

O primeiro experimento de cache observou redraw/back/forward/home de cerca de
16–18 s para 0,4–0,5 s em vistas já visitadas, com 2,5 MiB de RGBA retidos nas
três vistas do teste. **Vistas novas ainda custam a rasterização completa**:
nessa execução, aproximadamente 19–20 s para zoom/pan. O cache não resolve a
cobertura raster inicial, e composição rápida não significa pintura rápida.

A conferência final no wheel instalado observou 0,395–0,416 s para
redraw/back/forward/home e aproximadamente 16,6 s para novas vistas de zoom/pan,
com os mesmos limites, dimensões e índices de histórico da medição anterior.
As 54 composições anteriores permanecem na matriz original; os 12 cenários
novos estão em arquivos adicionais, preservando o exemplo e os testes existentes.

Relatórios: `real-geojson-benchmark-source.json` (anterior ao cache),
`real-geojson-benchmark-cache.json` (experimento inicial) e
`real-geojson-benchmark-wheel.json` (implementação final instalada).
São observações locais pequenas, com carga do computador não controlada,
sem garantia geral de tempo e sem inferir latência de apresentação física.
Tk usou widgets/event loop reais, janela oculta e input programático.

Reprodução no ambiente de desenvolvimento, após fornecer o arquivo:

```bash
python tools/benchmark_real_geojson.py municipios.geojson --output resultado.json --repeats 3 --tk
python tools/benchmark_real_geojson.py municipios.geojson --output navegacao.json --tk-only
```

Continuam pendentes cobertura raster inicial em bases detalhadas, apresentação
visível/input nativo, bases originais mais extensas e CI efetiva multiplataforma.
Este lote encerra subpassos verificáveis; não encerra os cinco critérios da 0.2.
