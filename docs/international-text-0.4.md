# Texto internacional — desenvolvimento da 0.4

A implementação original de composição da Azimlib integra motores tipográficos
genéricos opcionais. Não usa Matplotlib, Cartopy, navegador ou Pillow para decidir
como uma palavra deve ser composta. A versão estável publicada continua 0.3.0;
este guia descreve o código de desenvolvimento, ainda sem publicação.

## Instalação e uso

No checkout de desenvolvimento:

```bash
python -m pip install -e ".[text,png]"
```

HarfBuzz (`uharfbuzz`, Apache-2.0) fornece substituição/posicionamento OpenType;
fontTools (MIT) fornece acesso a fontes e contornos; aggdraw rasteriza os contornos.
ICU fornece propriedades Unicode, graphemes e identificação de scripts pela API C pública.
O resolvedor bidi é próprio da Azimlib, implementado a partir do UAX #9. No
Windows a biblioteca do sistema é usada; Linux precisa de `libicu` e macOS de
`libicucore` ou uma instalação de ICU disponível para o carregador do sistema.
Nenhuma DLL, tabela Unicode ou fonte adicional é baixada automaticamente.

```python
import azimlib as azl
# import azimlib.pyplot as plt também continua disponível.

with azl.text_context(language="ar", direction="auto"):
    fig, ax = azl.subplots()
    title = ax.set_title("القاهرة / Cairo")
    ax.text(31.24, 30.04, "العربية", fontsize=14, halo="white")

# A figura e os Artists capturam as opções, inclusive para ticks automáticos.
title.set_direction("rtl")
title.set_language("ar")
title.set_fontfeatures({"liga": 1})
title.set_visible(False)
fig.savefig("map.svg")
```

Também é possível passar `textengine="harfbuzz"`, `direction`, `language`,
`fontfallback` e `fontfeatures` diretamente aos textos. O engine `basic` permanece
o padrão sem contexto, sem dependências tipográficas adicionais. Os contextos
são isolados por thread/contexto e restaurados mesmo após exceções.
`get_capabilities("svg", textengine="harfbuzz").require("complex_shaping")`
verifica disponibilidade; não constitui certificação visual de uma plataforma.

## Contrato de composição

- Texto de entrada permanece em ordem lógica Unicode; não inverter manualmente
  árabe/hebraico. `_bidi.py` calcula níveis e runs visuais, incluindo números,
  pontuação, brackets, isolates, overrides e limites de profundidade do UAX #9,
  revisão 51. Não foi portado de outra implementação. Propriedades de caracteres
  e segmentação são fornecidas pelo ICU; suas versões efetivas são registradas.
- Índices públicos de clusters/runs são posições de code points Python. O binding
  converte explicitamente UTF-16, inclusive caracteres fora do BMP.
- A escolha de fallback exige cobertura do grapheme inteiro. Fontes adjacentes
  preservam contexto de shaping; marcas, ligaturas e conjunções índicas não são
  recompostas como caracteres isolados. Linguagem e features OpenType são explícitas.
- `ShapedLine`, `TextRun` e `Glyph` são imutáveis. Posições são em em; métricas,
  curvas, rotação, alinhamento, halos e DPI usam as mesmas unidades físicas dos
  componentes existentes. PNG, SVG, PDF e Tk/Qt consomem esses mesmos contornos.
- Ausência de engine/fonte/cobertura causa erro explícito. Não há troca silenciosa
  por `?`, tofu ou uma fonte instalada na máquina sem proveniência conhecida.
- Limites: 4096 code points por linha, 16384 glifos por linha, fonte até 32 MiB,
  registro de fontes até 128 MiB e tile de texto até 16 megapixels. Caches têm
  limites de entradas; esses limites não representam um teto global de RSS.

## Fontes e licenças

DejaVu original permanece incluída e inalterada. Árabe/hebraico e acentos usam sua
cobertura disponível; isso não implica cobertura CJK/índica universal.
Para outra fonte, o responsável deve fornecer origem pública, licença completa
e confirmar permissão de exportar contornos:

```python
record = azl.register_font(
    "MyFont-Regular.ttf", family="My Font",
    source="https://example.org/fonts/my-font/",
    license_id="OFL-1.1", license_text=complete_license_text,
    allow_outlines=True,
)
with azl.text_context(fallback=("My Font",)):
    fig, ax = azl.subplots()
    ax.set_title("Texto multilíngue")
```

Esse aceite é declaração do chamador, não uma conclusão jurídica automática da
Azimlib. O registro copia bytes em memória, registra SHA-256/copyright/cobertura
e impede substituição da família. Não exporta o caminho local. URLs de origem
não aceitam credenciais, query ou fragmento. Os bits OpenType de restrição de
embedding/bitmap-only bloqueiam este caminho; não substituem a licença da fonte.
São aceitas fontes estáticas TTF/glyf e OTF/CFF monocromáticas. Coleções TTC,
fontes variáveis não instanciadas e fontes coloridas/bitmap são recusadas.

As fontes Noto Devanagari/CJK de validação são opcionais, OFL-1.1, fixadas por
commit, tamanho e SHA-256 em `src/azimlib/data/optional-fonts.json`. Não integram
wheel/sdist. Aquisição explícita e verificável:

```bash
python tools/acquire_text_fonts.py --output optional-data/text-fonts
python tools/validate_text_engine.py --fonts optional-data/text-fonts --output text-review
```

Preservar as respectivas licenças e copyrights ao redistribuir fontes. Ver
[avisos de terceiros](../THIRD_PARTY_LICENSES.md) e
[inventário tipográfico](text-dependencies-0.4.json).

## Exportação, acessibilidade e viewers

| Saída | Política de texto complexo |
| --- | --- |
| PNG | Contornos posicionados, antialiasing e proveniência/licenças em iTXt; texto não selecionável |
| SVG | Contornos não dependem de fontes no leitor; texto lógico em `aria-label`/`desc`, licenças em metadata |
| PDF | Contornos e `ActualText` UTF-16BE por texto; avisos anexados; cópia/pesquisa dependem do leitor |
| Tk/Qt | Mesmo compositor/PNG; Artists, visibilidade, edição, pan/zoom e recompose próprios |
| HTML offline | Contornos existentes mantidos, tamanho físico preservado ao navegar; componentes dinâmicos mantêm o protocolo portátil existente |

SVG de shaping usa outlines: editar a string em um editor SVG não recompõe esses
paths. Editar o Artist Python e exportar novamente preserva texto lógico, fonte,
estilo e posição. `aria-label`/`desc` e PDF `ActualText` não são promessa de PDF/UA,
acessibilidade integral ou de seleção/pesquisa idêntica em todos os leitores.
Não são incorporados arquivos de fontes externas; os contornos e avisos bastam
para reproduzir o aspecto, dentro das permissões declaradas.

O HTML não contém ICU/HarfBuzz executável. Recomposição dinâmica de texto
arbitrário em scripts complexos exige o viewer Python; não se anuncia shaping
universal no JavaScript. Ticks/escala numéricos seguem o protocolo existente.
TeX completo, layout vertical CJK, quebra automática de parágrafos, hyphenation e
edição de cursor/seleção por glifo não fazem parte deste lote; TeX pertence à etapa 8.

## Curvas, colisões e validação

Labels em curvas usam clusters compostos em ordem visual e mantêm as formas
contextuais, ligaturas e offsets de marcas. A curva orienta cada cluster sem
separar a marca da base. Caixas de colisão incluem overhangs e métricas de todas
as fontes; prioridades, repetição e leader lines continuam usando o planejador
cartográfico próprio. Curvatura extrema pode rejeitar um candidato para preservar
legibilidade. Isso não equivale a deformar contornos de uma palavra ao longo da curva.

`tests/test_text_engine_040.py` compara glifos/advances/clusters com chamadas
diretas a HarfBuzz, testa bidi/graphemes/isolates, recusa de cobertura, CFF,
licenças/restrições, curvas, caches, componentes, rotação e DPI.
`tools/validate_text_engine.py` gera espécimes/mapas PNG/SVG/PDF, HTML, manifest e
capturas Tk/Qt quando solicitado. Os pacotes passam pelo auditor de privacidade.
O workflow manual `text-review-0.4.yml` prepara artifacts separados em Windows,
Linux e macOS. Não publica Pages, PyPI, release ou tag.

Conformidade reproduzível, com aquisição explícita de dados Unicode 15.1.0:

```bash
python tools/validate_unicode_text.py --data optional-data/unicode-15.1 --acquire --output unicode-conformance.json
```

Tamanhos e SHA-256 são fixados; os datasets não entram nos archives. A ferramenta
verifica todos os níveis, a ordem visual e graphemes: 91.707 casos de caracteres,
770.241 casos/modos por classes bidi e 1.187 casos de segmentação. Não há lista
de exceções que transforme falhas em sucesso. Apenas posições marcadas `x` pelo
formato oficial são omitidas na comparação, conforme X9. Isso não prova
conformidade com futuras versões de propriedades Unicode.

A validação inicial de `ubidi_*` encontrou 30 divergências nos casos de
overrides/isolates, brackets/marcas e profundidade, tanto no ICU do Windows
72.1.0.4 quanto no binário oficial ICU 78.3. Por isso o runtime não usa esse
resolvedor: o resolvedor próprio passou nos conjuntos oficiais completos de
níveis e ordem citados acima. Graphemes continuam no serviço ICU, verificados
separadamente. Fontes, HarfBuzz e rasterização têm seus próprios testes.

**7.08 permanece pendente**: testes locais e screenshots não substituem CI nos
três sistemas nem aprovação visual humana explícita de cada plataforma. A versão
do código e os hashes devem coincidir com os artifacts revisados antes do gate final.

Referências de API: [HarfBuzz](https://harfbuzz.github.io/),
[UAX #9](https://www.unicode.org/reports/tr9/tr9-51.html),
[ICU graphemes](https://unicode-org.github.io/icu-docs/apidoc/released/icu4c/ubrk_8h.html),
[fontTools pens](https://fonttools.readthedocs.io/en/latest/pens/index.html),
[OpenType fsType](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#fstype).
