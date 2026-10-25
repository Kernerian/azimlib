# Registro técnico — Fase C da 0.5.0.dev0

## Identidade e domínio

Branch dev/0.5.0; base preservada b77b12c92523d203211a3d30e39f09998e5d0816.
O commit que contém este registro identifica a implementação C. Relatórios
operacionais gerados depois do commit registram seu SHA e hashes dos outputs.
Não é release publicada nem aprovação visual humana presumida.

Contratos: [thematic-0.5.md](thematic-0.5.md). Checklist: **43/122 concluídos,
79 abertos**, inventário de 122 IDs preservado. Novos concluídos:
11.01–11.06, 12.01/12.02/12.04/12.05, 13.01/13.02/13.05 e 17.02.
As capacidades preparadas/parciais estão discriminadas na checklist.

## Evidência funcional

Testes test_thematic_assets_050.py, test_thematic_050.py e
 test_thematic_examples_050.py cobrem catálogo próprio, definições imutáveis,
SVG/PNG hostis e budgets, hash/proveniência, aspecto/ancoragem/rotação, tamanho
visual e largura métrica local, máscaras/furos, múltiplos componentes,
antimeridiano/horizonte/polos recusados, funções de gradiente e semântica,
Bézier analítico/spline C1, geodésica e adapter de rede, vetores/sprites/alpha,
determinismo, lifecycle, contexto, picking e clones isolados.

O primeiro snapshot de regressão local teve 1625 testes:1603 aprovados,22 skips,
zero falhas/erros. O endurecimento final do importador tem 49 testes temáticos
focados aprovados, incluindo a nova recusa de composição SVG não suportada.
As 498 verificações independentes congeladas B passaram; os quatro outputs
terrestres PNG/SVG foram idênticos byte a byte à0.4. Relatórios finais do pacote
instalado/CI retêm o SHA, contagens, skips e falhas sem substituir esse snapshot. Corpus e tolerâncias B
não foram alterados. Comparação terrestre usa PNG/SVG do snapshot publicado
0.4.0 em cenas regional e ortográfica. Não regenerar baselines para obter aprovação.

## Galeria e materiais

Oito cenas: atlas didático, exploração de Marte, catálogo, regiões/bandas/
gradiente, curvas/geodésica, grupos visíveis/ocultos e Terra/Marte.
PNG/SVG/PDF gerados pela Azimlib, com índice HTML local e gallery.json contendo
versão, SHA, dimensões/DPI, primitivas, tempos e SHA-256 de cada arquivo.

A base terrestre é Natural Earth, domínio público e avisos preservados.
Territórios/nomes locais/cidades/recursos/rotas editoriais são ficção autoral:
não reconstrução do Mali, mapa mineralógico ou rota de missão.
O cenário marciano usa campo sintético explícito por padrão. O parâmetro local
--real-data pode reutilizar o complemento B já auditado: imagem Viking MDIM2.1
colorizada, NASA Ames/USGS, servida pelo NASA/JPL Trek; frame histórico da
imagem explicitamente declarado, sem conversão implícita para orientação IAU.
A imagem não é DEM nem inferência de geologia/elevação. Nenhum novo download.
Arquivo preparado: mars-viking-512.png; o manifesto B fornece edição, origem,
licença, georreferência e hash. Dados reais não são incorporados ao pacote.

Os 18 símbolos nativos e dois assets pequenos dos exemplos são próprios,
BSD-3-Clause, Kernerian; hashes em examples/thematic/assets/provenance.json,
verificados pelo auditor de materiais. DejaVu e terceiros existentes conservam
suas licenças; não há bibliotecas externas de ícones ou código científico novo
copiado. Declaração de origem de assets fornecidos por usuários não constitui
verificação jurídica automática de titularidade.

## Performance e plataformas

benchmark_thematic.py: 600x400,100DPI,400 símbolos,128 vértices de região,
598 amostras de curva;3 warm-ups +12 repetições de cena/pan/zoom/toggle;
3 exportações por formato. Registrar todas as medições, mediana,p95 e variância,
memória Python separada do tempo. Não mede latência percebida do toolkit,
GPU ou garantia de FPS. Benchmarks são observações, não os budgets adiados 0.4.

smoke_thematic_tk.py: widget Tk nativo retirado, pintura de vetores/PNG,picking,
callbacks, toggles e remoção; eventos normalizados de teste não são aceite humano.
Workflow thematic-0.5.yml: mesma galeria sintética, testes, benchmark e Tk em
Ubuntu/Windows/macOS no mesmo SHA, sem publicação. CI geral e workflow B
continuam executando seus workloads existentes. Ausência de runner não é
regressão funcional nem aprovação. Consultar os resultados por SHA; não afirmar
execução nativa de outra plataforma com base na execução local Windows.

A Fase B permanece encerrada tecnicamente/funcionalmente com ressalvas:
Linux e Windows validados; macOS nativo no SHA b77b12c92523d203211a3d30e39f09998e5d0816
continua pendência externa, matriz B completa não aprovada. CI C não substitui
essa evidência histórica específica.

## Limitações e fronteira da Fase D

- SVG estrito; PNG pequeno; importadores não são navegador ou editor universal.
- Regiões angulares regionais; recusa de interiores globais/polares ambíguos.
- Gradiente amostrado; PDF rasteriza apenas seu preenchimento local (até1Mpx),
  não símbolos vetoriais, caminhos, contorno, texto ou página.
- Curvas editoriais não são científicas/orbitais; rede planetária não inventada.
- Labels associados simples; sem labels curvos, solver editorial, locators,
  seções de legenda, atlas completo ou temas de dados embutidos.
- Clipping retangular por grupo; máscaras poligonais por região, não clip
  poligonal universal de qualquer descendente. Clonagem de coleções legadas
  especializadas continua recusada; ownership mutável único sempre exigido.
- Navegação HTML recusa os novos payloads. PNG exige CPU/fallback declarado;
  nenhum contrato de performance GPU novo.
- Costuras ortográficas densas do PDF B permanecem refinamento histórico;
  costuras novas de gradiente C tratadas com tile localizado, de modo explícito.

Próxima fase recomendada: composição editorial D, com locators, labels e
legendas estruturadas. Não iniciada automaticamente. Os quatro gates
0.4.0/2.08,9.08,13.06,13.07 continuam formalmente adiados em seu registro original.
