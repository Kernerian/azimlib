# Current scope status — 0.4 development

The checkpoint below is **historical**, not the current acceptance dashboard.
7.08/8.08 subsequently received explicit three-system human acceptance;
their completion remains preserved. Four gates (2.08,9.08,13.06,13.07) are now
formally deferred, not passed. All eight stage-14 items await final delivery/
revalidation; 14.01/14.06 have historical evidence only.
[Current checklist](release-progress-0.4.md), [decision](deferred-gates-0.4.md),
[latest observed results](observed-validation-0.4.md).

## Original checkpoint, preserved

# Validação dos gates pendentes — 0.4.0

Checkpoint técnico, sem release. Nenhum dos seis IDs foi marcado como concluído
nesta rodada: 7.08/8.08 aguardam inspeção humana; 9.08 e 13.06/13.07 ainda têm
critérios quantitativos não satisfeitos; 2.08 exige o dump planetário integral.

## Texto e TeX — 7.08 / 8.08

Mesmo SHA **d61a3ca02739ce6d8f43de175b55de75ecec58dc**, branch de validação,
[execução 38176155877](https://github.com/Kernerian/azimlib/actions/runs/38176155877),
**6/6 jobs aprovados**. Esta execução específica não substitui a CI final de
release. Integridade de archives/arquivos, identidade dos sources entre sistemas,
conformidade Unicode, licenças e privacidade foram verificadas automaticamente.

| Sistema | Texto — 7.08 | TeX — 8.08 |
| --- | --- | --- |
| Linux | [artifact](https://github.com/Kernerian/azimlib/actions/runs/38176155877/artifacts/11715254429) | [artifact](https://github.com/Kernerian/azimlib/actions/runs/38176155877/artifacts/11716147217) |
| macOS | [artifact](https://github.com/Kernerian/azimlib/actions/runs/38176155877/artifacts/11715778227) | [artifact](https://github.com/Kernerian/azimlib/actions/runs/38176155877/artifacts/11716350085) |
| Windows | [artifact](https://github.com/Kernerian/azimlib/actions/runs/38176155877/artifacts/11715339332) | [artifact](https://github.com/Kernerian/azimlib/actions/runs/38176155877/artifacts/11715753784) |

Artifacts têm retenção de 30 dias. Extrair cada archive e abrir `index.html`.
Comparar o mesmo specimen/DPI/formato em todos os sistemas; não comparar imagens
100 dpi e 200 dpi como se tivessem o mesmo tamanho físico.

Checklist visual para aceite explícito por sistema:

- Texto: árabe conectado, direção RTL/LTR mista e números, scripts índicos,
  CJK, acentos/combining marks, símbolos e fontes de fallback sem caixas vazias.
- Métricas: baseline, rotação, alinhamento, halos, títulos/rótulos/ticks,
  espessuras físicas e margens em 100/200 dpi; PNG/SVG/PDF sem recorte inesperado.
- TeX: frações, integrais, somatórios, radicais, matrizes e texto misto;
  edição/exportações e recursos tipográficos creditados.
- Capturas das próprias janelas Tk/Qt e exports: mesmos componentes e ausência
  de regressão de layout. Capturas não comprovam interação física ou latência.

ICU/grapheme tests usam a versão normativa Unicode correspondente a cada
provider; selecionar fixture pelo contrato não remove casos que falharam.
TeX real foi executado com as ferramentas no ambiente ativo, além de verificar
a instalação isolada sem o extra. Cache só tolera a renomeação atômica temporária
durante aquisição monitorada; execução offline mantém verificações estritas.

**7.08 e 8.08 aguardam aprovação visual humana explícita.**

## GPU — 9.08

SHA **8959ff25c57786e487ec351bcd7615c954fbd569**,
[execução 38178094779](https://github.com/Kernerian/azimlib/actions/runs/38178094779),
**4/4 jobs aprovados**: contratos sem GPU nos três sistemas e referência Mesa.
[Mapa/terreno CPU/GPU](https://github.com/Kernerian/azimlib/actions/runs/38178094779/artifacts/11717395182),
[volumes](https://github.com/Kernerian/azimlib/actions/runs/38178094779/artifacts/11716717539).
Hashes, fontes idênticas entre os dois artifacts, licenças e scans de privacidade
verificados. Mesa é software; não comprova desempenho de hardware.

[Profiling detalhado](gpu-profile-0.4.json) e [método](gpu-0.4.md).
Windows, RTX 2060, NVIDIA 617.42, Python 3.14.4; workload fixo de 24 quadros/fase.

| Medida sequencial scene→image | Antes, mediana | Depois, mediana |
| --- | --- | --- |
| Pan | 197.284 ms | 68.799 ms |
| Zoom | 761.301 ms | 160.443 ms |

Primeira pintura sequencial caiu de 971.642 para 471.444 ms. Paridade média
CPU/GPU fica em aproximadamente 1.2/255 por canal, com bordas não idênticas.
Indexação da legenda e construção/packing em lote preservam regras geométricas,
caps/joins/dashes, supersampling e budgets; NumPy permanece opcional.

Composição/preparação de CPU, submissão de buffers, comandos GPU temporizados e
espera/readback estão separados no diagnóstico. Consultas síncronas perturbam
o scheduling; não usar esses tempos como benchmark normal. DMA/PCIe puro, VRAM
do driver, HID físico e scanout do compositor não foram isolados.
Eventos nativos sintéticos→pintura Tk/Qt também excedem 100 ms em várias amostras.
Os limites de **33 ms/quadro** e **100 ms/interação** não foram alterados.
**9.08 permanece pendente.**

## Eclipses — 13.06 / 13.07

[Contrato científico e reprodução](eclipse-precision-0.4.md),
[resumo quantitativo](eclipse-validation-0.4.json).
Leitor SPK próprio e reduções experimentais internas; efeméride bruta externa,
clocks/frame/discos/umbra/penumbra separados, sem certificação herdada do kernel.

302 posições centrais e 601 coordenadas de borda comparadas, além de doze
contatos lunares e dois controles sem eclipse. 2023 excede 2 km na trajetória
e 3 km em 29 bordas. Falta um orçamento global sustentado e validação dos
contatos solares absolutos; a API independente tentou retornar os dados mas
estava inacessível. Sucessos lunares não encerram os dois IDs.
O auditor científico retorna 3; limites/casos continuam congelados.

## Planeta — 2.08

[Procedimento integral preservado](planet-trial.md). Implementação, extrato real,
streaming, referências em disco e limites já foram validados. Falta exclusivamente
o ensaio real com `planet.osm.pbf`, em infraestrutura adequada, antes do gate
final. Nenhum download planetário nesta rodada; extrato não substitui o planeta.
O protocolo registra data/SHA-256, EOF, contagens, referências perdidas/corruptas,
tempo, picos RAM/disco, limites impostos e resumo verificável.

Essa pendência não bloqueia frentes independentes, nem autoriza encerramento
da versão. A etapa 14, a versão estável e os fluxos de publicação foram preservados.
