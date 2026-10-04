# Aceite local do passo 4 — 2026-10-03

Os itens **4.08–4.10** encerram o corte de desempenho com medições reproduzíveis,
pixels preservados, input humano confirmado e limites explícitos. Não prometem
FPS constantes, primeira vista instantânea ou desempenho igual ao Matplotlib
em qualquer mapa. A validação das outras plataformas permanece no passo 5.

## Base original, perfil e mudança

Foi usada a [malha municipal original de São Paulo, IBGE 2024](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/UFs/SP/):
645 municípios, **892.336 posições**, GeoJSON de 22.894.192 bytes. Todas as
coordenadas XY fornecidas foram conservadas, sem simplificação. A conversão de
desenvolvimento usa apenas a biblioteca padrão; não acrescenta leitura pública
de Shapefile. [Proveniência, hashes e CRS](original-geojson-provenance.json).
O CRS original é SIRGAS 2000: não foi realizada transformação de datum para
WGS84. É uma avaliação de visualização esférica, sem promessa de precisão cadastral.
Os dados externos não são incluídos no wheel, sdist ou ZIP fonte.

O perfil da geometria original apontou cobertura de strokes/discos como maior
gargalo: 82,3 s instrumentados em `CoverageDraw.polygon`, dentro de 106,0 s
instrumentados. Esses valores de cProfile **não são** os tempos sem profiler
da tabela abaixo. [Resumo do perfil](detailed-profile-before.json).

O extra `accelerate` compila os loops numéricos **da Azimlib** com Numba/NumPy
genéricos. Não inclui outro renderer, Matplotlib, engine GIS, fastmath, redução
de vértices ou cache persistente de código. Construção de segmentos, tracejados,
discos, caps/joins e polígonos continua própria; a ordem das interseções e da soma
de áreas é preservada. Sem o extra, permanece o caminho escalar Python/Pillow.
O custo inicial do compilador está incluído nas medidas frias.

```bash
pip install "azimlib[gui,accelerate]"
```

## Rasterização precisa e memória

Windows 11 build 26200, Ryzen 5 5600X (6 núcleos/12 threads), CPython 3.14.4,
Pillow 12.3.0, NumPy 2.5.3, Numba 0.68.0, llvmlite 0.50.0. Figura 6,4×4,8
polegadas; além da malha original, mesh sintético 47×35 células, cinco níveis
de contorno e 1.200 pontos determinísticos. Sem janela durante estes timings.

| Vista / DPI | Raster antes | Raster atual | Redução local | Pico WSS antes → atual |
|---|---:|---:|---:|---:|
| Completa / 100 | 60,42 s | 33,58 s | 44,4% | 320 → 433 MiB |
| Deslocada / 100 | 57,99 s | 31,11 s | 46,4% | 321 → 434 MiB |
| Foco / 100 | 20,38 s | 11,81 s | 42,0% | 267 → 354 MiB |
| Completa / 200 | 90,43 s | 33,42 s | 63,0% | 487 → 559 MiB |

Duas amostras em processos novos por configuração; mediana do raster e maior
pico WSS observado. Os oito pares finais têm **RGBA e PNG byte a byte idênticos**.
Não é inferência de significância estatística nem garantia em outra máquina.
O custo de compilação/runtime aumenta memória: o commit privado chegou a cerca
de 794 MiB no caso de 200 DPI. WSS/commit vêm de `GetProcessMemoryInfo`, não de
tracemalloc; são valores do processo, com seus módulos e buffers, não só da imagem.

Os relatórios `detailed-before-*-r*.json` preservam o runtime anterior;
`detailed-final-*-r*.json` medem o runtime atual. Os `detailed-after-*-r*.json`
são uma etapa intermediária com limiar de compilação 256 e cache de 8 MiB,
**não** o runtime final. Seus snapshots permanecem em `tools/baselines`.
[Auditoria consolidada](performance-acceptance-audit.json) confere hashes, origem
dos módulos, input, pixels e memória sem repetir os timings.

## Preparação de vistas novas, distinta do cache de imagens

O LRU de paths projetados passou de 8 para **16 MiB de payload**, mantendo
1.024 entradas máximas. A malha original ocupa 14.455.285 bytes em 702 entradas:
o orçamento anterior a expulsava durante cada percurso, provocando reprojeção
completa em todo pan. Não se alteraram precisão float64 nem composição.

| Composição | Antes | Atual |
|---|---:|---:|
| Primeira vista | 9,01 s | 8,52 s |
| Pan novo | 9,09 s | 0,41 s |
| Segundo pan novo | 9,14 s | 0,37 s |
| Retorno Home | 8,31 s | 0,38 s |
| Retorno ao pan | 8,49 s | 0,35 s |

São vistas sucessivas reais no mesmo processo, **sem cache de Scene ou imagem**.
Os cinco hashes da Scene, incluindo floats e estilos, coincidem antes/depois.
[Antes](detailed-new-views-before.json), [atual](detailed-new-views-after.json).
16 MiB limitam o payload retido; não limitam a memória total. Outras bases
maiores ainda podem expulsar entradas. A primeira preparação continua em segundos.

## Janela visível e input humano

A verificação visual Windows cobriu Pan com saída/retorno, zoom, Home,
Voltar/Avançar e fechamento, sem saltos ou mudança de espessura no exemplo
Brasil. O escopo não inclui a base municipal pesada nem outras plataformas.

[Telemetria final do Brasil](visible-navigation-brazil.json): 1.606 eventos
nativos, 26 press/release, dez wheel, três Home, 12 Back, quatro Forward e 246
registros de pintura idle do Tk. Handler máximo 31,1 ms; intervalo máximo do
heartbeat 108,5 ms; idade estimada do despacho mediana 0 ms/máximo 63 ms, sujeita
à granularidade do timer nativo. Entrega PhotoImage/canvas mediana 5,5 ms.

Para 31 eventos cuja vista exata foi entregue antes da próxima mudança de
extent, input→idle teve mediana 210 ms, p95 551 ms e máximo 782 ms. Vistas
intermediárias coalescidas não entram nessa amostra; uma revisita posterior não
é contada como latência do evento antigo. Scene usa (west,south,east,north),
enquanto Axes usa (west,east,south,north); a auditoria normaliza essa ordem.
**Idle do Tk não mede compositor, vsync ou apresentação física no monitor.**
O script preservado em `tools/baselines/visible-navigation-human` corresponde
exatamente ao hash da sessão humana, anterior à opção de demonstração por API.

Na [janela detalhada](visible-navigation-detailed.json), duas mudanças pela
API própria, pan novo e retorno Home, mediram entrega/pintura do Tk em canvas
visível. **Não houve input humano nessa sessão.** A primeira preparação/raster
levou cerca de 48 s antes de disponibilizar a janela; o pan novo estabilizou em
35,14 s e o retorno Home em 1,69 s usando o frame preciso armazenado. O maior
intervalo do heartbeat foi 2,00 s. A primeira entrega ocorreu antes do canvas
ficar mapeado; somente as mudanças seguintes têm `canvas_viewable=true`.
Retorno de cache não representa velocidade da primeira rasterização.

O quadro preciso pesado permanece em worker próprio após navegação; sua
conclusão leva dezenas de segundos, e composição/cópia ainda podem causar pausas.
A abertura inicial é síncrona. **O caso de 892 mil posições não tem aceite de
pan contínuo fluido.** Ele delimita o teto medido deste corte, sem bloquear o
aceite do viewer Brasil nem esconder um gargalo futuro.

Não houve captura automática do desktop. Observação visual Windows e
resultados da instrumentação são evidências separadas.

## Reprodução e escopo do aceite

Na raiz do projeto, prepare a entrada externa uma vez e execute sem outras
cargas pesadas concorrentes. A ferramenta de preparação baixa apenas a entrada
oficial selecionada para o benchmark, verificando formato e hashes; ela não integra o runtime.

```bash
python tools/prepare_original_benchmark.py --help
python tools/benchmark_detailed_map.py caminho/ibge-sp-original-2024.geojson --output raster.json --warm
python tools/benchmark_new_views.py caminho/ibge-sp-original-2024.geojson --runtime src --output views.json
python tools/measure_visible_navigation.py --output native-input.json
python tools/audit_step4.py
```

O benchmark aceita `--runtime` para comparar snapshots próprios preservados,
`--view whole|pan|focus` e `--dpi 100|200`; cProfile usa `--profile` em uma
execução separada. Sem entrada externa, o auditor ainda confere os relatórios
distribuídos. Não se impõe um teste de tempo frágil à suíte.

A suíte completa passou: **675 testes/22.192 subtests**, em 187,385 s, com
compilador opcional disponível. As seis novas regressões/5.470 subtests comparam
bits de áreas/interseções, máscaras, linhas finas, acumulados, fallback e pixels
com alpha/tracejados/buracos/recortes em duas resoluções; também permanecem os
testes de cancelamento, processos de navegação e orçamento/cache existentes.
Tempo de suíte não é benchmark de navegação. CI do extra foi configurada,
mas não é declarada executada remotamente.
[Registro dos checks source/wheel](performance-acceptance-checks.json): 39
testes selecionados com compilador e os mesmos 39 sem ele (dois checks
exclusivos do compilador pulados), onze checks Tk de pan e 28 de toolbar
em cada runtime; 114 exports estáticos iguais à distribuição anterior.

O aceite fecha **evidência, melhoria e limites** de 4.08–4.10. Abrange as bases
e resoluções descritas, não novos formatos, datum cadastral, GPU, dados urbanos,
3D ou navegação fluida arbitrariamente densa. No encerramento deste lote havia
sete subpassos do passo 5 pendentes, incluindo CI efetiva e verificações nas
demais plataformas. A contagem atual está na [checklist](release-progress.md).
