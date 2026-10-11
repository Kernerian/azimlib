# TeX real — desenvolvimento 0.4

A opção TeX usa o **Tectonic** para compor um fragmento LaTeX e o executável
**pdftocairo** para converter sua saída PDF em contornos. A Azimlib interpreta
esses contornos e os desenha em seus próprios renderers PNG, SVG e PDF.
Não importa Matplotlib, não usa seu backend e não incorpora sua implementação.
O parser interno de expressões `$...$` continua separado e limitado.

## Instalação e seleção explícitas

```bash
pip install 'azimlib[tex,png]'
```

O extra instala apenas ferramentas Python genéricas: fontTools, psutil e
aggdraw. **Não instala Tectonic, Poppler, pacotes TeX ou fontes.** Instale os
executáveis separadamente pela distribuição de sua escolha, confira suas
licenças e prepare um cache Tectonic local antes de usar a API. A biblioteca
sempre passa `--only-cached` e `--untrusted`; falta de recursos causa erro.

```python
from pathlib import Path
import azimlib as azl

font_notice = azl.Provenance(
    source="https://example.org/my-fonts",  # substitua pela origem real
    license="OFL-1.1",                    # licença real das fontes usadas
    copyright="Copyright do titular das fontes",
    license_text=Path("font-license.txt").read_text(encoding="utf8"),
)
config = azl.TexConfig(
    executable="tectonic",
    converter="pdftocairo",
    cache_dir=Path("tex-cache"),
    preamble=r"\usepackage{amsmath}\newcommand{\area}{A}",
    trusted=True,
    allow_outlines=True,
    font_notices=(font_notice,),
)
with azl.tex_context(config):
    fig, ax = azl.subplots()
    ax.map("brazil")
    title = ax.set_title(r"Área $\area=\int_{\Omega} dA$")
fig.savefig("map.svg")
title.set_text(r"Atualizado $\frac{a}{b}$")
fig.savefig("updated.pdf")
```

Forneça avisos completos para **todas** as fontes usadas pelo preâmbulo. O
exemplo acima é um modelo de configuração, não uma declaração de origem ou
permissão para uma fonte real. A biblioteca exige confirmação de permissão
para exportar contornos; essa confirmação e os avisos não provam titularidade.
`import azimlib.pyplot as plt` usa o mesmo estado e as mesmas APIs.

Para um Artist individual, use `textengine="tex", texconfig=config`.
`artist.set_texconfig(config)` ativa o motor; `get_texconfig()`, `set_text()`,
visibilidade, tamanho, cor, alinhamento e rotação continuam editáveis.
Um contexto é local à execução/thread e as figuras capturam sua configuração.

## Cobertura

- Fragmentos LaTeX com matemática, frações, integrais, somatórios, radicais,
  matrizes, macros e preâmbulo explicitamente fornecido.
- Um fragmento por linha de texto; blocos multilinha são compostos pela
  Azimlib. O resultado aceito contém glifos preenchidos e regras retas
  monocromáticas. A cor/transparência/halo pertencem ao Artist.
- Métricas reais de largura, altura e profundidade; baseline alfabética,
  alinhamento, rotação e tamanho físico compartilhados pelos três formatos.
- O TeX seleciona fontes no documento/preâmbulo. `fontfamily` da tipografia
  básica não seleciona automaticamente uma fonte TeX equivalente.
- Recursos gráficos arbitrários, imagens, conteúdo SVG ativo, referências
  externas, caminhos traçados curvos, clipping TeX e páginas adicionais não
  integram este contrato de fragmentos. Conteúdo não suportado causa erro.
  A opção não é um editor/exportador de documentos LaTeX completos.
- Labels TeX podem ser posicionados/rotacionados como blocos. Não são
  fragmentados em caracteres para seguir uma curva.

Tectonic compila TeX real. Isso não significa que qualquer pacote LaTeX ou
qualquer saída gráfica possível seja aceito pelo contrato vetorial da Azimlib.
Veja [a CLI oficial do motor](https://tectonic-typesetting.github.io/book/latest/v2cli/compile.html)
e [os formatos do conversor](https://manpages.debian.org/trixie/poppler-utils/pdftocairo.1.en.html).

## Recursos, segurança e diagnósticos

Use apenas **entrada TeX, preâmbulos, fontes e executáveis confiáveis**.
`trusted=True` torna esse contrato explícito. `--untrusted` desabilita recursos
inseguros conhecidos do motor, mas não transforma TeX em um sandbox de sistema
operacional. Não ofereça esta API diretamente a texto enviado por desconhecidos.
Para isso, use isolamento externo com cotas de CPU/RAM/disco e acesso a arquivos
e rede restrito. A biblioteca não promete impedir todo acesso a arquivos de um
processo confiável, de um pacote TeX ou de um executável modificado.

Cada compilação usa um diretório temporário removido ao terminar. Não usa shell,
shell escape ou instalação automática. Configuração/cache de aplicação e
temporários são direcionados explicitamente; no Windows a variável de perfil
registrado é preservada porque a API de diretórios conhecidos exige isso.
Logs brutos permanecem no temporário e não entram em exceções ou exports.

Os limites padrão são 30 s por ferramenta, 1 GiB de RSS somado da árvore de
processos, 64 MiB/4096 arquivos no temporário e 256 MiB no cache de recursos.
RAM/disco são **amostrados**; não são cotas rígidas de kernel. Estouro/timeout
encerra o processo e os descendentes observados. São aceitos até 4096 caracteres
por fragmento, 8192 no preâmbulo e um subconjunto SVG com limites próprios.

`TexUnavailableError` indica ferramenta/cache ausente. `TexError` indica erro
de compilação, glifo ausente ou saída incompatível; `TexResourceError` indica
limites excedidos. Nenhum erro troca silenciosamente para outro motor.
Somente `fallback="basic"` solicita explicitamente a tipografia básica,
com aviso Python; expressões que excedem o parser interno ainda podem falhar.

## Cache, viewers e proveniência

Fragmentos preparados contêm métricas/contornos imutáveis e podem ser enviados
ao worker do viewer sem executar TeX nele. A composição Python recompila textos
alterados; mudanças de cor, posição ou rotação reutilizam contornos. O navegador
HTML exibe os contornos preparados e não executa TeX: editar fórmulas ou gerar
novos labels TeX exige recomposição em Python.

O cache usa texto, tamanho físico, estilo, preâmbulo, configuração, hashes dos
executáveis e do cache de recursos/fontes. `clear_tex_cache()` força nova leitura.
São retidos até 128 fragmentos/16 MiB de payload imutável medido. Em cada
composição Python, ferramentas/recursos são conferidos uma vez e novamente ao
terminar; mudanças durante a composição causam erro. Não há invalidação por TTL.
Arquivos locais de recursos precisam permanecer estáveis durante uma composição.
Se o preâmbulo carregar fontes/arquivos fora do cache, liste-os explicitamente
em `resource_files=(Path("resource-file"), ...)` para incluir seus hashes na
identidade. Não use descoberta de fontes do sistema ou entradas externas não
declaradas em uma composição que precise ser reproduzível.
Os exports preservam origem/licença das fontes e identidade dos recursos/motores,
sem caminhos de configuração. SVG mantém descrição textual e PDF `ActualText`;
isso não garante pesquisa/cópia matemática semântica ou conformidade PDF/UA.

## Reprodução da validação

O cenário de referência usa Tectonic 0.17.0, pdftocairo 26.07.0, Latin Modern
(GUST Font License/LPPL) e Computer Modern Type 1 da AMS (OFL-1.1). Não inclua
esses executáveis, cache ou fontes nos archives Python. Licenças/versões de
referência estão em [tex-dependencies-0.4.json](tex-dependencies-0.4.json) e
[avisos de terceiros](../THIRD_PARTY_LICENSES.md).

Uma aquisição de desenvolvimento **separada e explícita**, com limites de
recursos/reserva de disco, prepara as fontes e pacotes desse cenário:

```bash
python -I tools/prepare_tex_cache.py --engine tectonic --converter pdftocairo --cache tex-cache --report acquisition.json --acquire
python -I tools/validate_tex.py --engine tectonic --converter pdftocairo --cache tex-cache --output tex-review
```

O snapshot de [validação local e hashes](tex-validation-0.4.json) registra a
suíte cumulativa, contratos TeX, fontes e exports Windows. O workflow manual
`tex-review-0.4.yml` está preparado para gerar artifacts Linux/macOS/Windows;
preparar esse workflow não significa que ele já foi executado.
O item 8.08 exige validação nos sistemas suportados. Uma execução local Windows
e imagens geradas não encerram esse gate multiplataforma.
