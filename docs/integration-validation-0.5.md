# Evidência técnica integrada — 0.5.0.dev0

Branch dev/0.5.0,sem publicação. O commit que contém este registro consolida
somente documentação/evidência após o snapshot funcional
f410159dc06abe74517964c712fbd3bdb8cf5636. Os relatórios operacionais finais
externos identificam o novo SHA, CI e hashes dos pacotes reconstruídos.
Uma aprovação de snapshot não é aprovação presumida da revisão seguinte.

## Snapshots e regressões

- Lucide0ae3af1151a642c28dc66f0fc0189f2036959784:30 SVGs upstream fixados.
- D6409fb8e7d506db1dde9287e4e29635c5441b337: composição editorial comum.
- E400fadb40a8eb362328fbc78cc54878694a81e1d: aplicações planetárias finitas.
- Integração9c5f47d7886edc7742da8d49641ed4af1164197a e correções de tooling
  c9d4d439a624a067eb535908a8a1860c1694f822/e60d5eb37fa8452386e328f9e6819c3ae31fc2a0.
- Cache exato e cobertura tipográfica f410159dc06abe74517964c712fbd3bdb8cf5636.

Regressão local Windows/Python3.14.4:1670 testes executados,1648 aprovados,
22 skips,zero falhas/erros,23612 subtests. Contagem anterior C1626: acréscimo
44 testes Lucide(14),editorial(14),aplicações(10),integração(6). Skips originais
preservados; não redução de testes/tolerâncias. O run restrito que encontrou
WinError10013 nos quatro testes HTTP foi repetido integralmente com loopback
permitido e passou. Não é execução nativa de Linux/macOS.

498 verificações independentes B aprovadas,mesmo corpus/tolerâncias. Quatro
outputs terrestres PNG/SVG de cenas regional/ortográfica são byte a byte
idênticos à0.4.0 preservada. Verificador/baselines não regenerados para aprovação.
135 arquivos protegidos(histórico0.4,dados,fontes,ícones antigos,licenças e
relatórios A/B/C) mantiveram bytes. Novas licenças ficam em arquivos separados.

## Validação nativa especializada no mesmo SHA funcional

| Workflow | Evidência | Estado |
|---|---|---|
| Superfícies | [40454069410](https://github.com/Kernerian/azimlib/actions/runs/40454069410) |3/3 Ubuntu,Windows,macOS |
| Primitivas | [40454069498](https://github.com/Kernerian/azimlib/actions/runs/40454069498) |3/3 Ubuntu,Windows,macOS |
| Integração D/E/F | [40454069419](https://github.com/Kernerian/azimlib/actions/runs/40454069419) |3/3 Ubuntu,Windows,macOS |

O workflow integrado executa testes0.5,contratos de labels/texto/TeX/rotação,
corpus498,18cenas em PNG/SVG/PDF,benchmarks e widgets Tk/Qt nativos com input
sintético. TeX aqui é regressão de contrato com skips explícitos conforme
instalação; não nova certificação de toda engine/font externa ou aceite humano.
Artifacts recuperados tiveram SHA/54hashesdeoutputs por plataforma conferidos,
mais os relatórios Tk/Qt aprovados. Revisão visual nova continua pendente.

A matriz principal de28jobs tem relatório próprio e precisa terminar aprovada
no SHA final de desenvolvimento; não inferir seu sucesso das9aprovações acima.
Nenhum job não executado é contado como aprovado. A primeira falha F foi de
preparação do diretório de saída; correção explícita,métodos intactos.
A pendência histórica B/macOS em b77b12c92523d203211a3d30e39f09998e5d0816
permanece aberta,sem aprovação retroativa pelo novo SHA.

## Performance observada,sem contrato de33/100ms

Workload editorial fixo120ícones com halo/sombra suave+120labels,1região,
rota598pontos,legendaseccional e locator,1000x700/100DPI,CPUAMD64/Python3.14.4.
Warmup2,8amostras de preparação e2exports; bruto/mediana/p95/variância/RSS
nos relatórios. Runs diagnósticos pré-checkpoint tiveram outras atividades de
QA locais; não são comparação laboratorial isolada nem benchmark do SHA final.
O resultado final deve ser registrado separadamente com seu SHA real.

| Operação | Mediana antes | Mediana após cache | p95 após |
|---|---:|---:|---:|
| Preparação quente |1916.6ms|237.1ms|246.2ms|
| Pan+locator |1905.4ms|194.1ms|216.5ms|
| Zoom+locator |2238.7ms|179.1ms|208.3ms|
| ExportPNG completo |5448.9ms|2669.8ms|2702.5ms|
| ExportSVG completo |2315.6ms|233.8ms|239.3ms|
| ExportPDF completo |2512.0ms|309.9ms|317.2ms|

RSS observado~75MB,não pico global. Perfil instrumentado caiu de8.29M chamadas/
6.184s para0.95M/0.401s; tempos instrumentados não equivalem ao benchmark.
A rasterização repetida de máscaras dominava; o LRU exato elimina esse trabalho,
sem reduzir vértices/tolerâncias ou aproximar o frame. Testes frios/quentes
comparam pixels e forçam evicção. Ainda não é garantia de fluidez em cenas densas.

## Auditorias e pacotes

Licenças/proveniência verificam30Lucide,ISC e Feather MIT,duas cópias legais
verbatim com SHA b495047bd93a9b06913511076f504daba17d5bbeb3e0650f3bb53a4220329c57.
Código original BSD3-Clause; NaturalEarth,DejaVu,CC0,ColorBrewer e avisos
opcionais preservados. Não há nova dependência obrigatória nem downloader.
Auditor de distribuição reconhece a expressão conjunta de terceiros,sem
relicenciar o código original paraMIT.

Wheel/sdist locais verificam conteúdo exato,RECORD,metadata,licenças,ausência de
bibliotecas GIS runtime,dados volumosos e arquivos privados. Instalação isolada
sem dependências opcionais exercita APIs antigas+Lucidevetorial/página/labels/
locator/grupos/geodésica/comparação. Softshadow requer Pillow explicitamente.
Auditoria técnica de privacidade inclui fonte,arquivos compactados e histórico/
refs locais; não promete detecção infalível nem erasure remota.

Os pacotes do commit de registro devem ser reconstruídos,auditados,instalados e
receber hashes no relatório operacional final. Nenhum pacote foi publicado.
20.07 permanece aberto pois CI/pacotes não substituem revisão humana final.

## Estado de entrega

**98/122 concluídos,24abertos**,com122IDs/critérios originais preservados e
sem novos adiamentos formais. [Checklist](release-plan-0.5.md) discrimina cada
pendência científica,leitor,mosaico,matriz adversa e papel de tema ainda parcial.
19.06/20.07 aguardam revisão humana;20.08 aguarda autorização/publicação futura.
O snapshot é desenvolvimento tecnicamente demonstrado no recorte declarado,
não release candidate integralmente encerrado ou autorização de publicação.
Os quatro gates0.4,main,tag,Release,pacotes publicados e Pages foram preservados.
