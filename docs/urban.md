# Cartografia urbana — após a 0.2.0

Requisito registrado: trabalhar com **cidades, bairros, ruas e edificações**.
Prioridade definida: implementar esse roteiro **depois da 0.2.0**, junto de
3D e das demais expansões futuras; a consolidação 2D atual vem primeiro.
Esta é uma evolução planejada da frente de formatos/dados, simbologia e
desempenho; não significa que bases urbanas ou APIs específicas já existam.

Hoje, geometrias fornecidas em GeoJSON podem usar o núcleo próprio:
`geojson`, `roads(data)`, `scatter`, estilos por feature, labels e polígonos.
Isso permite desenhar dados urbanos, mas ainda não oferece um sistema urbano
completo, seleção por endereço, bases locais detalhadas ou cálculo de trajetos.

## Sequência de implementação

1. **Dados e contratos.** Um exemplo urbano real, com fonte/licença/versão/CRS
   explícitos e carregamento local reproduzível. Separar localidades/pontos,
   limites de cidades, bairros, vias e footprints de edifícios. Uma cidade
   pode representar uma localidade ou um limite administrativo conforme a
   fonte; essa diferença precisa ficar explícita nos metadados.
2. **Camadas familiares.** Aproveitar os Artists e estilos por atributo
   existentes para vias por classe, limites e áreas de bairros, construções
   e pontos de interesse. Estudar métodos de conveniência sem criar outro
   modelo de figura, axes, legendas ou colorbars. Os nomes finais da API
   devem ser definidos na implementação, com testes de uso.
3. **Escala e rótulos.** Exibir cidades, bairros, ruas e POIs conforme a vista;
   priorizar nomes, controlar colisões e direção dos nomes nas vias. Espessura
   em pontos e largura física em metros precisam ser opções distintas e
   documentadas, com escala e símbolos legíveis em zoom próximo.
4. **Navegação detalhada.** Medir o índice/culling/cache próprio com dados
   urbanos reais, incluindo muitos polígonos de edifícios e nomes. Validar
   pan/zoom, seleção regional, overview e eixos compartilhados; medir tempo,
   memória total e latência da GUI separadamente da exportação.
5. **Recursos posteriores.** Seleção/picking de feições, busca local por nome,
   redes/roteamento com topologia explícita, relações complexas de dados e
   novos leitores próprios. Extrusão/altura de edifícios depende da futura
   fundação 3D; um footprint 2D não implementa essa capacidade.

Dados pesados devem ficar em pacotes opcionais ou arquivos fornecidos pelo
usuário, com download explícito quando houver integração. Mapas temáticos
urbanos usarão os mesmos mappables, normalizadores, legendas e colorbars.
Matplotlib seguirá somente como referência de interface/comportamento; o
trabalho geográfico e a renderização continuarão no núcleo da Azimlib.
