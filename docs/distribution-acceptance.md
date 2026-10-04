# Validação e distribuição — 5.06–5.09

> Evidência histórica: resultados CI, tempos e hashes abaixo pertencem aos
> snapshots originais. A preparação BSD/licenças/privacidade altera arquivos;
> os checks atuais e a relação de hashes publicados estão em
> [preparação de publicação](publication-readiness.md). Esses resultados não são uma nova execução CI.

**5.08 e 5.09 concluídos no pacote 0.1.0 alpha deste corte.** A versão não foi
alterada para 0.2.0. **5.06 e 5.07 permanecem abertos**: naquele registro não havia CI remota e a execução local cobria apenas Windows. Os resultados locais
não são rotulados como execução remota nem como validação das outras plataformas.

## Nome, metadados e conteúdo — 5.08

O [lookup exato do PyPI](package-name-check.json) retornou HTTP 404 para o nome
normalizado `azimlib` em 2026-10-03, horário local. É uma observação naquela
consulta, sem reserva do nome ou garantia futura de permissão para upload.
Nenhum pacote desconhecido com esse nome foi instalado. Os metadados continuam
anunciando 0.1.0/alpha e Python >=3.10. Conta/permissão PyPI e URL real do
repositório ainda precisam existir antes de publicar; não foram inventadas.

O auditor novo confere:

- Nome/versão/Python/SPDX do METADATA contra pyproject; todos os extras/markers
  em Python 3.10, 3.11 e 3.14. Dependências obrigatórias continuam vazias.
- Todos os arquivos runtime/recursos byte a byte no wheel e sdist; todos os
  arquivos entregáveis de docs/tests/tools/examples no sdist/ZIP fonte.
- RECORD: lista completa, tamanho e SHA-256 de cada entrada do wheel.
- Seis camadas Natural Earth com gzip, hashes e contagens conferidos;
  quatro fontes upstream DejaVu inalteradas e licença incluída;
  21 assets de toolbar próprios, com fonte/geometria BSD-3-Clause.
- Licenças registradas no relatório histórico presentes e expressão SPDX coerente. Cores CC0 têm
  autores e origem no NOTICE_COLORMAPS; dados têm manifesto e termos separados.
- Ausência de imports cartográficos externos no runtime; ausência de ambientes,
  caches, credenciais/dados de desenvolvimento e malha original IBGE nos pacotes.
- `twine check --strict` aprovou wheel/sdist, incluindo o README em Markdown.

Fontes, dados e escopo: [upstream das fontes](fonts-upstream.json),
[dados incluídos](data.md), [assets originais](toolbar-icons-audit.json).
O auditor compara conteúdo/licenças registrados; não é parecer sobre marcas
nem autorização para publicação em contas externas.

```bash
python -I tools/audit_distribution.py --wheel dist/azimlib-0.1.0-py3-none-any.whl --sdist dist/azimlib-0.1.0.tar.gz --output audit.json
python -m twine check --strict dist/*
```

O JSON de hashes dos arquivos finais fica **ao lado dos artefatos**, fora dos
archives, evitando hash autorreferencial. Reexecutar a auditoria após 5.10/5.11:
uma auditoria 0.1.0 não valida automaticamente os futuros bytes de 0.2.0.

## Suíte e instalação isolada — 5.09

[Resultados locais](release-validation-local.json) guardam ambiente, origem
instalada, versões genéricas, módulos/hashes, skips, logs e resultados separados.
O runner usa `-I` e exige o pacote instalado dentro do venv; não acrescenta
o checkout ao sys.path. A instalação GUI Python 3.11 foi feita em venv novo.

| Ambiente Windows | Execução | Resultado |
|---|---|---|
| Python 3.11.9 / Tk 8.6.12 / Pillow 12.3 / NumPy 2.4.6 | Suíte inteira do wheel GUI | 675 testes / 16.792 subtests, sem falhas; dois checks exclusivos de Numba pulados |
| Python 3.14.4 / Tk 8.6.15 / Pillow 12.3 / NumPy 2.5.3 | Suíte inteira do wheel GUI | 675 testes / 16.792 subtests, sem falhas; os mesmos dois skips |
| Python 3.14.4 / NumPy 2.5.3 / Numba 0.68 | Kernel compilado + contratos de pan | 11 testes / 5.470 subtests, sem falhas e sem skips |
| Python 3.11 e 3.14 | Integração desktop instalada | 13 scripts Tk por versão, com retorno de processo/logs/relatórios separados |
| Venv core novo / instalação offline | SVG/HTML/dados/fontes/edição/componentes | Smoke completo aprovado sem Pillow, NumPy, Matplotlib ou GIS |

O primeiro smoke de layout excedeu o limite de 300 s nas duas versões. Esses resultados de falha foram conservados. Apenas esse smoke foi repetido com prazo de 900 s: passou em 331 s (3.11) e 328 s (3.14), com 30 checks/18 frames por versão. Os outros 12 scripts já haviam passado. Runtime, pixels e assertions não mudaram; ampliar o prazo do runner não é ganho de desempenho. O runner agora encerra sua própria árvore de processos em timeout; a limpeza também foi conferida com um timeout intencional de um segundo, registrado como teste negativo.

Os skips acima são explícitos e foram cobertos na execução com compilador.
A suíte source anterior com o compilador passou 675 testes/22.192 subtests;
não se somam execuções repetidas como se fossem novos testes. As durações das
suítes concorrentes não são benchmarks de desempenho.

O guia inicial também foi executado em source, core isolado e GUI instalado;
os nove SVGs coincidem. A galeria instalada reproduz 19 exemplos em PNG/SVG/HTML.
[Galeria e metodologia](release-gallery.md), [limites do corte](visual-differences.md).
Não há Matplotlib/GIS instalado nos venvs GUI/core usados para este aceite.
O compilador e os validadores de pacote são opcionais, não dependências do núcleo.

## O que falta nas plataformas — 5.06 e 5.07

A CI tem 24 jobs e conserva logs/JSON mesmo em falha. Agora usa o mesmo runner
verificado localmente, com build, auditoria de wheel/sdist, core offline e
smokes desktop. O Linux dispõe de setup explícito de Xvfb/xauth. A definição
YAML foi conferida; nenhuma execução GitHub Actions ocorreu naquele registro histórico.
[Guia para criar o repositório e iniciar a matriz](ci-setup.md).

| Plataforma | Suíte instalada/contratos Tk locais | Janela com input humano | Estado restante |
|---|---|---|---|
| Windows | Python 3.11 e 3.14 executados | Observação visual Windows dos passos 3/4, runtime do viewer preservado | CI remota nas versões declaradas ainda necessária |
| Linux | Nenhuma execução local; WSL não instalado | Pendente | CI e conferência nativa |
| macOS | Nenhuma execução local/host disponível | Pendente | CI e conferência nativa |

Para conferir o relatório retido contra o runtime atual: `python -I tools/audit_release_validation.py`. Logs completos permanecem na pasta local de trabalho; hashes e resultados estão no JSON distribuído.

Os smokes Tk ocultos verificam handlers, Subplots/toolbar/save/exportação e
fechamento, sem aprovar a aparência ou input físico em Linux/macOS. O aceite
humano Windows permanece em [3.08](viewer-visible-acceptance.md) e no
[registro do passo 4](performance-acceptance.md), com resultados separados dos testes automatizados.
O roteiro de 54 IDs mantém essas duas pendências separadas da auditoria e
instalação já concluídas. Versão/changelog finais e instalação 0.2.0 ficam
em 5.10–5.12 após os requisitos anteriores.
