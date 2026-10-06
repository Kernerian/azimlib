# Aceite Azimlib 0.2.0

> Evidência histórica: resultados CI, tempos e hashes abaixo pertencem aos
> snapshots originais. A preparação BSD/licenças/privacidade altera arquivos;
> os checks atuais e a relação de hashes publicados estão em
> [preparação de publicação](publication-readiness.md). Esses resultados não são uma nova execução CI.

**Azimlib 0.2.0 pronta; passo 5 encerrado, 54/54 IDs concluídos.** A [matriz da versão 0.2.0](ci-0.2.0.json) aprovou 24/24 jobs no commit 65697cab58fe949fe6a75057f670c89c6eea9feb. Cada relatório remoto identifica o pacote instalado, SHA dos módulos, logs e eventuais skips; todos os SHA de Python coincidem com o runtime entregue. Publicação no PyPI não realizada.

## Correções verificadas

A [execução inicial](https://github.com/Kernerian/azimlib/actions/runs/37177546418) falhou em instalação 3.10, hash de fonte Python no checkout Windows, eventos sintéticos incompatíveis com macOS e liberação de Tcl no raster worker Windows. O [PR #1](https://github.com/Kernerian/azimlib/pull/1) corrige essas quatro causas.

- aggdraw >=1.3.19 tem wheels Python 3.10; >=1.4 exigia >=3.11. Pip seleciona a versão compatível; cartografia/render de geometria continuam próprios.
- .gitattributes fixa LF de Python e preserva bytes de recursos/baselines. O hash da geometria dos 21 ícones continua obrigatório; nenhum teste de integridade foi ignorado.
- Os fixtures usam num=2/state=512 para botão direito no macOS, mantendo o botão lógico RIGHT=3 e as mesmas assertions de pan/histórico. O conversor de eventos já distinguia plataformas.
- Fechamento libera imagens/variáveis/widgets/Tcl no thread UI, inclusive editor Subplots. A thread raster não fica responsável pelos finalizadores de um viewer já fechado.

[Primeira matriz corrigida](ci-portability-fix.json): **24 jobs aprovados**, quinze suítes instaladas de 675 testes/16.792 subtests (dois skips do compilador explícitos), seis jobs de 11 contratos/5.470 subtests sem skips e treze scripts Tk por sistema. Build, twine strict, RECORD/fontes/dados/ícones e core offline também aprovados. Não somar repetições como testes novos.

Validação local adicional: Windows/Python 3.11 com aggdraw 1.3.19 passou 675 testes; 28 checks toolbar, 13 viewer e 30 layout/18 frames passaram em Python 3.14. Suítes/tempos concorrentes não são benchmarks.

## Plataforma e aceite humano

O escopo de plataforma combina observação visual Windows e CI nos três sistemas. Aceite visual e input humano Windows dos passos 3/4 permanecem registrados. Tk Linux/macOS usa janela oculta/Xvfb e eventos sintéticos na CI: **não existe conferência visual nativa humana nessas duas plataformas**. Essa é uma limitação explícita posterior ao corte, sem relabelar testes como experiência física.

## Pacote e limites

0.2.0 conserva o núcleo sem dependências obrigatórias, extras png/gui/accelerate/dev genéricos, dados Natural Earth generalizados, quatro fontes DejaVu upstream e 21 ícones originais BSD-3-Clause. Fontes/dados têm proveniência e licenças incluídas. Malha municipal externa original IBGE, ambientes de desenvolvimento e credenciais são excluídos.

Os arquivos de [validação 0.1.0](release-validation-local.json) e galeria anterior permanecem históricos, com snapshots exatos; não aprovam automaticamente o pacote novo. Os hashes dos archives finais ficam ao lado dos arquivos, fora dos archives, evitando autorreferência.

[Diferenças visuais/API](visual-differences.md), [limites de contornos](contour-boundaries.md), [desempenho observado](performance-acceptance.md), [projeções/dados](math.md). Relevo 3D, urbano, novos formatos/datum completo e demais expansões seguem [o roteiro posterior](pending.md). Publicação 0.2.0 no PyPI concluída em 2026-10-06; veja o [registro verificado](release-publication-0.2.0.md).

## Artefatos e reprodução final

[Instalação local 0.2.0](release020-local-validation.json): venv core novo instalado offline, venv GUI novo, versão de distribuição e runtime coerentes, nenhum Matplotlib/GIS instalado e todos os 111 arquivos runtime/recursos idênticos. Treze checks viewer, 28 toolbar e 11 pan passaram no wheel. [Galeria 0.2.0 instalada](release020-gallery.json): 19 exemplos/57 arquivos em 100 DPI, PNG/SVG/HTML idênticos ao catálogo anterior. Os exemplos/checks são repetições verificadas, não testes novos.

Build 0.2.0 e twine strict aprovados; auditoria confere METADATA/extras/SPDX, RECORD/tamanhos/SHA, licenças, quatro fontes, seis camadas e 21 ícones, além da ausência de dados externos/ambientes. Os hashes definitivos wheel/sdist/ZIP ficam no relatório `azimlib-0.2.0-distribution-audit.json` ao lado dos artefatos. O ZIP fonte completo conserva previews offline; o ZIP GitHub menor omite a galeria gerada.

Mudanças posteriores ao commit de CI são apenas documentação/resultados, sem mudar runtime, dependências, workflow ou assertions. O relatório cita o commit que de fato executou a CI; não transforma uma atualização documental em outra execução remota.
