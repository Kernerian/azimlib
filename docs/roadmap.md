# Roteiro da Azimlib

A **0.3.0 está publicada**: [registro de entrega e hashes](release-publication-0.3.0.md).
A 0.2.0 conserva seu [registro histórico](release-publication-0.2.0.md) e
[checklist concluída](release-progress.md).

A **[checklist da 0.3.0](release-progress-0.3.md)** é a fonte única de passos,
subpassos e evidências: 10 passos, **80/80 concluídos**, 80 IDs estáveis. O
[inventário](pending.md) liga todas as 16 frentes anteriores a esse corte.

A 0.3.0 amplia urbano/formatos/CRS, Transforms/Artists/layout, raster/campos,
acabamento e exportação, interação/integração/desempenho, terreno 3D experimental,
tempo/atlas e documentação/distribuição. Começa pela [fundação urbana](urban.md).

3D e tempo não são nomes para o globo ortográfico 2D existente: exigem câmera,
oclusão e lifecycle próprios, descritos nos passos 8 e 9.

As reservas da 0.3.0 integram o inventário da 0.4.0: volumes/GPU, PBF,
CRS/grids, topologia, geocodificação/roteamento e TeX/shaping, dentro da cobertura
documentada. A comprovação planetária, os budgets completos GPU e a certificação
global de eclipses foram formalmente adiados, sem aprovação dos critérios.
Nenhuma cobertura universal ou data de conclusão desses gates é prometida.

Runtime cartográfico independente; novas bases de terceiros conservam suas
próprias licenças. Não há downloads implícitos nem promessa de compatibilidade
integral com todos os toolkits do Matplotlib.

## Proposed additions for 0.4–0.6

See [terrestrial Sun/Moon, Beyond Earth and Orbits](future-versions.md) for the
new cumulative proposals and accuracy/licensing gates. The original reserved work stays inventoried; four gates are explicitly deferred
by the [approved development rescope](deferred-gates-0.4.md), not marked passed.

## Próximo corte

A [checklist operacional da 0.4.0](release-progress-0.4.md) reúne as seis reservas
da 0.3.0 e as propostas novas de Sol/Lua: **14 etapas e 112 IDs preservados**.
Estado: 104 concluídos, quatro adiados e quatro pendentes de entrega/revalidação;
14.01/14.06 foram revalidados localmente; CI e artifacts exatos permanecem abertos.
Contagem atual, dependências, evidências por lote e critérios ficam somente nessa
fonte. A prova planetária de 2.08 permanece pendente. Não há prazo prometido.
Beyond Earth permanece proposto para 0.5.0;
Orbits, para 0.6.0. Manutenção cartográfica, urbana e de plataformas é contínua.

0.4.1: correções compatíveis, refinamentos e ensaio planetário se houver
infraestrutura. 0.5.0 mantém Planetary Cartography / Beyond Earth; renderer e
ciência podem evoluir como fundações, sem exigir certificação global de eclipses.
0.6.0 mantém Orbits. [Registro de adiamentos e critérios](deferred-gates-0.4.md).
