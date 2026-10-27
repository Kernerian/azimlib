# Integração técnica 0.5.0.dev0 — Lucide / D / E / F

Snapshot de desenvolvimento em dev/0.5.0. Não é autorização nem release.
As evidências finais externas ao pacote identificam o commit exato, plataforma,
versões, hashes e resultados. Não armazenar logs de runner com caminhos pessoais
na documentação de produto. Os snapshots anteriores não foram reescritos.

## O que foi implementado

Lucide1.61.0,30 SVGs oficiais inalterados e locais,upstream
c29c276f16590cf017126671535ad8c792be64d8. Catálogo recomendado com nomes
oficiais e aliases cartográficos explícitos. Catálogo original e assets próprios
continuam disponíveis. Nenhum JavaScript/download em importação/renderização.
Origem,ISC/Feather MIT,hashes e texto verbatim em assets/lucide/manifest.json,
licenses/Lucide.txt e cópia distribuída. Ver THIRD_PARTY_LICENSES.md.

```python
import azimlib as azl
fig, ax = azl.subplots(body=azl.MARS)
ax.set_extent((-20, 20, -15, 15))
ax.symbols([(0, 0)], 'lucide:bot', size=18, stroke_width=1.5,
           halo=azl.IconHalo(color='white', width=.8),
           shadow=azl.IconShadow(alpha=.2, offset=(.8,.8), blur=.6))
ax.set_theme('planetary-exploration')
```

Halo largura0..8pt; sombra offset<=16pt,blur0..8pt; efeitos opcionais sem mudar
âncora/coordenada/shape principal nem picking. Traço Lucide em unidades do
viewBox é independente da largura física do halo. Escala mantém proporção.

[Editorial D](editorial-0.5.md): insets independentes,footprints inversos,
links explícitos,legendas seccionais,fluxos com unidade,modelo de página,
labels/contextos/obstáculos e temas. [Aplicações E](applications-0.5.md):
feições e nomenclatura com origem/época/incerteza,sequências finitas e comparação
física ou normalizada de mundos. Não há renderer paralelo.

## Matriz real de formatos

| Elemento | PNG | SVG | PDF |
|---|---|---|---|
| Lucide/vetor,halo,sombra dura | raster final | paths vetoriais | paths vetoriais |
| Sombra suave de ícone | RGBA local | imagem alpha local + ícone vetorial | imagem alpha local + ícone vetorial |
| Ícone PNG customizado | raster | imagem local,demais vetores preservados | imagem local,demais vetores preservados |
| Áreas/rotas/hatches/locators | raster final | vetores | vetores |
| Gradiente autoral de região | bandas amostradas | bandas vetoriais | tile alpha local |
| Imagem orbital RGBA projetada | raster final | células vetoriais | tile por imagem para evitar costuras |
| Terreno/mesh3D | raster final | malha projetada | malha projetada,limites conhecidos |
| Texto simples padrão | glyph raster | texto semântico/editável | outlines + ActualText |
| Texto HarfBuzz/TeX | glyph raster | outlines/semântica declarada | outlines/ActualText conforme engine |

Tiles de efeito limitados a1Mpx,imagem orbital PDF a4Mpx. Não há rasterização
silenciosa da página inteira. Vetores ao redor da imagem/gradiente permanecem
vetores. Antialiasing/fontes/leitor podem variar entre plataformas; não prometer
identidade pixel a pixel universal. Texto curvo complexo exige clusters/shaping;
Math/TeX curvos são recusados, usar bloco tangente. HTML portátil não oferece
navegação temática/editorial: recusa explícita em vez de remover conteúdo.

O refinamento PDF trata imagens orbitais; não altera silenciosamente a malha
3D científica. Costuras de meshes ortográficas ainda podem ocorrer conforme
leitor/antialiasing e continuam registradas. Grades planetárias dos novos atlas
são discretas. Imagens orbitais reais são textura, não DEM medido.

## Execução reproduzível local

```bash
python -m pip install '.[dev,gui,qt,text,tex]'
python -m unittest discover -s tests -v
python tools/validate_planetary_surfaces.py --output qa/scientific.json
python tools/build_gallery_050.py --output qa/gallery
python tools/benchmark_thematic.py --output qa/benchmark-c.json
python tools/benchmark_editorial_050.py --output qa/benchmark-def.json
python tools/smoke_editorial_native.py --backend tk --output qa/tk.json
python tools/smoke_editorial_native.py --backend qt --output qa/qt.json
python tools/audit_licenses.py --report qa/licenses.json
```

Workflow integrated-0.5.yml: mesmos testes/corpus/18cenas/benchmarks nos runners
nativos Ubuntu,Windows,macOS,Python3.14. A matriz principal continua separada.
Linux Tk/Qt usa Xvfb real no runner nativo; não é benchmark de GPU física.
Jobs não executados/indisponíveis nunca equivalem a aprovação.
A pendência B/macOS no SHA b77b12c92523d203211a3d30e39f09998e5d0816 permanece
histórica e aberta mesmo se o novo SHA passar nesse sistema.

## Performance sem promessa de latência

CPU padrão. Workload C fixo400símbolos,região128vértices,path598amostras,
mais stress1000símbolos/depth8/doisviewports. Workload editorial1000x700/100DPI,
120símbolos+120labels+halo+sombra suave,região,path598,legenda2seções e locator.
Dois warmups,oito medições de preparação/pan/zoom/toggle e duas de cada export.
Relatórios retêm amostras,mediana,p95,variância,RSS observado e pico tracemalloc.
P95 com oito amostras é o máximo amostral, não estimativa robusta de produção.
Memória rastreada é alocação Python, não pico total do processo.

O protocolo é diagnóstico,sem toolkit presentation nem resposta física/GPU.
Cenas densas de labels/sombras podem custar segundos; não prometer fluidez
por ter renderizado um mapa. Planejamento de colisão agora reutiliza índices
espaciais por conjunto de exclusões e a cópia de estilo retorna snapshot
independente, evitando atravessar ownership/objetos internos.
A meta adiada0.4/9.08 não foi herdada nem considerada aprovada.

## Precisão e operações recusadas

498 verificações independentes B e tolerâncias congeladas continuam referência
para modelos estáticos esféricos/oblatos demonstrados. A galeria não certifica
ciência: crateras/geologia/recursos/rotas temporais são autorais e identificados.
Original Earth defaults,imports raiz/pyplot,CPU,lifecycle,picking e callbacks
continuam sujeitos à suíte integrada. Os quatro gates adiados0.4 permanecem
intactos; GPU/eclipses experimentais,PBF regional,nenhum ensaio planetário.

Não implementados: geodésia triaxial/irregular,planificação universal de malha,
datum vertical entre missões,orientação temporal sem kernels sustentados,
atmosfera física,previsão operacional e motor orbital0.6. Pesquisa aberta
não foi promovida a suporte, nem convertida em adiamento formal novo.

## Migração e revisão

symbol_catalog() recomenda Lucide; symbol_catalog('original') preserva o antigo.
Nomes oficiais lucide:*; original:* força o catálogo próprio. Aliases antigos
podem usar o equivalente Lucide recomendado; ivory/battle próprios continuam
identificados como desenhos Azimlib. Scripts que dependam do shape antigo devem
pedir original:* explicitamente. Seleção de cor/tamanho continua granular.

Galeria consolidada: PNG/SVG/PDF de18cenas,índiceHTML e manifestodehashes.
Índices externos separam Windows/Linux/macOS e preservam galerias anteriores.
Novos símbolos/efeitos,atlasTerra/Marte,locators,Lua/Vênus/Mercúrio,comparações,
terreno/perfil e exploração exigem revisão humana.19.06/20.07/20.08 permanecem
abertos. A checklist mantém122IDs; interfaces parciais e pesquisa não são entrega.
Pacotes dev locais não são release candidate autorizado nem publicação.
