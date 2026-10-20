# Roteiro da Azimlib

Estado deste documento: planejamento de desenvolvimento, atualizado em
2026-10-18 em branch separada da versão publicada. Não modifica documentação
congelada, artifacts, tag ou Release de versões anteriores.

## Histórico entregue e limites preservados

- **0.2.0**: [registro histórico](release-publication-0.2.0.md) e
  [checklist](release-progress.md), 54/54 itens.
- **0.3.0**: [registro](release-publication-0.3.0.md) e
  [checklist](release-progress-0.3.md), 80/80 itens. As
  [16 frentes anteriores](pending.md) permanecem como inventário histórico.
- **0.4.0 publicada**: 108 itens ativos concluídos + quatro formalmente adiados,
  preservando os 112 IDs. O [snapshot da checklist fonte](release-progress-0.4.md)
  preserva 107 concluídos e 14.08 unchecked; a conclusão real está no
  [recibo operacional público](https://kernerian.github.io/azimlib/publication-0.4.0.json),
  não em alteração retroativa do candidato/tag.

Os quatro gates **0.4.0/2.08**, **0.4.0/9.08**, **0.4.0/13.06** e
**0.4.0/13.07** permanecem no [registro de adiamentos](deferred-gates-0.4.md),
com critérios, budgets, tolerâncias, falhas e evidências intactos. Não se tornam
concluídos, nem bloqueios automáticos da 0.5.0. GPU segue experimental sem
garantia geral de 33 ms p95/100 ms; eclipses sem certificação científica global;
PBF validado regionalmente, sem ensaio integral planetário comprovado.

## 0.4.1 — manutenção e refinamentos compatíveis

Correções de regressão, compatibilidade, documentação e refinamentos sem
reformulação pública ampla. Ensaio planetário somente com infraestrutura
adequada; sem baixar planet.osm.pbf nesta máquina. Melhorias compatíveis de
GPU/ciência podem entrar, mas não existe promessa de encerrar gates científicos
nessa versão. Manutenção urbana/cartográfica e de plataformas continua.

## 0.5.0 — Planetary Cartography / Beyond Earth

Fase A de fundação implementada e validada localmente; próximas fases abertas.
[Contratos](foundation-0.5.md), [evidência](foundation-validation-0.5.md). Identidade principal Beyond
Earth, com camada temática/histórica/educacional/editorial integrada à mesma API
e reutilizável entre Terra e demais corpos.

| Frentes | Escopo preservado/ampliado |
|---|---|
| 1–3 | Body público, coordenadas/referenciais e projeções/geodésia por corpo |
| 4–6 | Raster/relevo extraterrestre, feições/geologia e iluminação |
| 7–10 | Exploração/tempo, comparação, API existente e dados/precisão/proveniência |
| 11–13 | Símbolos georreferenciados, áreas temáticas e rotas/fluxos/curvas |
| 14–16 | Insets/locators, composição editorial e labels/anotações avançados |
| 17–19 | Grupos compatíveis, temas reutilizáveis e exportação multiplataforma |

A [proposta consolidada](proposal-0.5.md) preserva todas as dez frentes antigas
e acrescenta nove, com contratos, dependências e riscos. A
[checklist de desenvolvimento](release-plan-0.5.md) preserva **122 IDs: 29
concluídos e 93 abertos**. São 19 frentes e uma etapa transversal.
Os contratos efetivamente implementados das [superfícies da Fase B](surfaces-0.5.md)
não promovem geodésia triaxial/irregular ou orientação temporal não demonstradas.
Recortes/interfaces preparados não são conclusão das funcionalidades futuras.

Sequência sugerida:

1. Contratos de Body/frame/unidades/API/proveniência e ownership/grupos.
2. Superfícies: projeções, geodésia, raster/relevo e iluminação por corpo.
3. Primitivas comuns: símbolos, áreas, caminhos e grupos, com casos Terra/Marte.
4. Composição: insets, labels, legendas, layout e temas.
5. Aplicações: geologia, exploração e comparação de mundos.
6. Exportação, matriz de plataformas, exemplos, migração e evidências futuras.

Exemplos propostos: `examples/thematic/historical_trade_map.py` e
`examples/planetary/mars_exploration_map.py`, compartilhando primitivas; Lua,
Vênus e comparação com Mercúrio complementam a cobertura. Dados devem ser
próprios, públicos/licenciados ou sintéticos identificados; não copiar assets
protegidos de ilustrações de referência.

Não criar editor gráfico/GIS desktop, motor orbital paralelo ou previsão
científica certificada implícita. Geodésia triaxial/irregular e planificação de
malhas exigem limites próprios e podem permanecer pesquisa explícita; nenhuma
operação não demonstrada pode ser chamada de entregue. Qualquer reescopo
posterior exige decisão registrada, não retirada silenciosa de frentes.

## 0.6.0 — Orbits

Preservar o [planejamento orbital](future-versions.md): mecânica orbital e
cenas espaciais, corpos hierárquicos, referenciais, trajetórias físicas,
iluminação/ocultações delimitadas, navegação e tempo. Reusar os Bodies, Artists,
seleção, câmera, tempo e exportação, sem duplicar representações.

Rotas editoriais, geodésicas e de rede na 0.5.0 não são trajetórias orbitais.
Não prometer N-body de alta precisão, planejamento operacional de missão ou
otimização de transferências. Certificação global de eclipses não é
pré-condição obrigatória da 0.5.0 ou automática da 0.6.0.

## Regras comuns de evolução

Runtime cartográfico independente; dados, fontes, ícones e ferramentas externas
conservam suas próprias licenças. Sem downloads implícitos, claims universais de
precisão/performance ou promessa de compatibilidade integral com outro toolkit.
Promover APIs experimentais somente com evidência adequada e migração quando
necessária. Publicação exige autorização futura específica; este plano não a concede.
