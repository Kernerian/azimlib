# Evidência de implementação — 0.5.0 Fase A

Esta é uma entrega de desenvolvimento, não a publicação da 0.5.0 nem a
conclusão de suas 19 frentes. Inventário: **17/122 concluídos; 105 abertos**.
Branch `dev/0.5.0`, derivada do planejamento
`d8be79df838ffa362dcf4f9e9f4e3bf32ee7666b`. O commit de implementação e os
resultados finais estão no [registro estruturado](foundation-validation-0.5.json).
Implementação base: `ed5b0fb75c76354e57655fea0d501a80a9db8b1c`; revisão de
limites de entrada: `2fd0f73997d67a4d7ee193f68bc2f82e2bf3c17d`. A revisão documental final
preserva o mesmo runtime validado.

## Rastreabilidade dos critérios concluídos

| IDs 0.5.0 | Implementação / evidência |
|---|---|
| 1.01–1.04 | `bodies.py`: modelo imutável, quatro formas explícitas, cinco presets, registro local; Bodies050 |
| 1.05–1.06 | Único Body público/interno, WGS84 preservado; Bodies050, regressão foundation_040 e corpus numérico independente |
| 2.01–2.03 | `planetary.py` e frames existentes: coordenadas estáticas, unidades, datum/frame/época, inversas e recusas; Coordinates050 |
| 2.05–2.06 | Sem transformação temporal implícita; relógios anteriores preservados; fixtures CSPICE, polos, radial triaxial e convenções adversas |
| 9.01 | Figure/Axes/Artists/GeoJSON contextualizados, defaults Terra e ownership; PlotContext050 |
| 9.03–9.04 | Lifecycle, picking, callbacks, stale, imports, CPU e opcionais; Groups050, regressão ampla e instalação local sem extras |
| 9.05 | CapabilityStatus e recusas por modelo/backend; guia da fundação e testes de falhas antes de attach |
| 9.06 | Regressão Terra, isolamento de contextos/transformações, exportações comparadas à 0.4.0 |
| 17.01 | ArtistGroup sobre a lista plana existente, hierarquia sem ciclos, ownership único; Groups050 |

Os critérios originais permanecem escritos na checklist. Os demais recortes
de 2.04, 8, 9.02, 10, 17 e 20 estão descritos como progresso parcial, mantendo
os respectivos itens abertos. Não foram implementados os mapas editoriais
completos, os insets planetários físicos, temas ou operações de superfície.

## Corpus numérico estático

As tolerâncias foram fixadas no guia antes da geração das fixtures:
XYZ/altura **1e-7 m**, ângulos **1e-10 grau**. O corpus tem 25 casos de
conversão normal-altura, cinco por preset: equador, latitude média, quase polo,
hemisfério sul, altura negativa rasa e altura elevada. A referência é
CSPICE_N0067 `georec`, via SpiceyPy 8.3.0, sem dependência desses pacotes na
execução dos testes congelados. Há também casos analíticos cardinais e uma
interseção radial triaxial conhecida, além de unidades/longitude adversas.

Erros máximos observados nas fixtures CSPICE: XYZ **3.726e-9 m**, altura
**2.794e-9 m**, ângulos **1.066e-14 grau**. São erros de aritmética estática
em superfícies ideais do corpus; não precisão de efemérides, de orientação IAU,
de coordenadas de missão ou certificação científica planetária global.
Origem/versões e entradas/saídas estão em `tests/fixtures/planetary-050.json`.

## Compatibilidade terrestre e formatos

O Brasil com estados/rota/escala/orientação/legenda e o globo ortográfico com
grade foram executados com a mesma cena, dimensões, DPI e ambiente contra
`50b467e252afe314645c031629ed1729007b267c` (fonte 0.4.0 publicada).
As quatro saídas SVG/PNG foram idênticas byte a byte. Isso é evidência dessas
duas cenas, não uma promessa de igualdade universal entre plataformas.

As quatro demonstrações da fundação foram geradas em SVG, PNG e PDF e
inspecionadas localmente. O exemplo de Marte usa somente coordenadas
sintéticas e carta angular não métrica. A comparação de dois corpos declara
que as dimensões dos painéis não comparam tamanhos físicos. O exemplo de
grupos demonstra estado visual independente sobre geometria compartilhada.

## Reproduzir

```sh
python -m unittest discover -s tests -p 'test*050.py' -v
python -m unittest discover -s tests -v
python examples/planetary/foundation_050.py --output foundation-demo
```

Execute no ambiente de desenvolvimento com a fonte instalada ou `src` no
PYTHONPATH. As demonstrações PNG exigem o extra png já existente; SVG e a
fundação Body/coordenadas/grupos não introduzem dependências obrigatórias.
Na suíte ampla, os testes opcionais declaram seus skips e requisitos próprios.

## Limites da evidência e próxima fase

Esta rodada valida localmente Windows/Python 3.14. Não executa CI hospedada,
não aprova visualmente Tk/Qt em três sistemas e não mede desempenho GPU.
Dependências opcionais ausentes não são consideradas aprovadas por analogia.
Grupos/contextos planetários recusam GPU nesta fase; Earth sem grupos preserva
o renderer anterior. Clipping de grupo só força o retângulo de Axes. Clonagem
de grupos só aceita Layers geométricos simples, sem transforms/mapping/callbacks
de estilo. As instâncias visuais nunca são compartilhadas entre viewports.

A Fase B deve começar pela matriz de superfícies/projeções, unidades físicas e
domínios, com validação independente por modelo. Raster/terreno e geodésia
planetários ainda exigem trabalho próprio. Triaxial normal/irregular e orientação
temporal permanecem recusados; não são aproximações esféricas ocultas.

0.4.0, seus quatro gates adiados, o escopo Beyond Earth e o roteiro Orbits 0.6
continuam preservados. Nenhum gate de publicação é executado nesta fase.

## Resultado local final

- Suíte ampla: **1.531 testes**, 1.509 aprovados, 22 skips explícitos,
  zero falhas/erros; 23.240 subtestes. Duração observada: 342,63 s.
- Fundação: **36/36** testes, incluindo modelos, conversões, isolamento,
  transforms incompatíveis, grupos/lifecycle e quatro demonstrações.
- Skips: GPU físico/ensaio explícito (15), Numba (2), TeX externo (3),
  fixtures opcionais de fontes (1) e permissão de symlink (1).
- Instalação isolada do wheel dev, sem rede/dependências obrigatórias: imports
  raiz/pyplot, coordenadas, Terra/Marte, SVG, grupos e recusas passaram.
  Pillow, NumPy, ModernGL, SpiceyPy e Matplotlib estavam ausentes nesse ambiente.
- Verificação local dos links: 144 documentos Markdown, 1.263 destinos locais,
  nenhum link local quebrado. Links remotos/âncoras não foram certificados.
- Licenças anteriores: 21 textos/avisos verificados; seis camadas geográficas,
  quatro fontes e dois recursos de métricas/colormaps com hashes preservados.
  Os novos parâmetros/fixtures têm proveniência explícita, sem kernel incorporado.

Uma rodada intermediária teve quatro erros de acesso HTTP loopback por restrição
do ambiente. Após habilitação do acesso local, os 36 testes de integração do
bridge passaram e a suíte ampla final foi repetida sem esses erros. Logs brutos,
relatórios de distribuição e hashes dos pacotes de teste ficam fora da fonte;
não há publicação de caminhos locais ou rastros privados de execução.

Os binários dev são somente evidência privada de instalação/packaging. Não são
um candidato final de release nem um aceite dos itens 19.05/19.06/20.07/20.08.
