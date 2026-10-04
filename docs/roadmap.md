# Próximas etapas

O [plano de implementação priorizado](next-steps.md) começa por qualidade
visual, composição, rótulos e navegação, antes das novas fundações 3D.
O [escopo de 0.2.0](release-0.2.md) consolida o núcleo 2D por cinco critérios
de conclusão. A versão atual permanece 0.1.0 alpha; não há data comprometida.

0.1 estabelece as interfaces e oferece mapas funcionais, dados reais offline,
SVG/PNG, viewer desktop Tk e HTML opcional, seis projeções e mapas temáticos. Não é uma biblioteca
GIS madura nem um substituto completo do Matplotlib.

1. **Robustez cartográfica:** clipping esférico generalizado, polígonos maiores
   que um hemisfério, topologia, operações de overlay, geodesia elipsoidal,
   CRS adicionais e viewports que atravessam a longitude ±180°.
2. **Escala de dados:** índice espacial, simplificação com erro em pixels,
   compartilhamento de fronteiras, cache de projeção e renderização incremental.
3. **Formatos:** leitores próprios de Shapefile/DBF e KML, CSV de pontos e
   leitores de rasters georreferenciados e resampling; ampliar os campos escalares,
   hillshade e contornos já disponíveis.
4. **Estilo:** padrões customizados além das dez hachuras atuais, ícones externos, múltiplos sistemas
   de unidades, regras de rotulagem de linhas e simbologia complexa.
5. **API/GUI:** ampliar compatibilidade de Artists, callbacks, atualização
   Python ↔ HTML, offsets científicos, objetos Tick completos, handlers de legenda, ampliar o layout
   de GridSpec/spans existente para grids aninhados/subfigures e criar backend Qt próprio.
6. **Distribuição:** auditoria dos nomes e licenças, documentação versionada,
   documentação hospedada, benchmarks contínuos, política semver e publicação no PyPI.

Hachuras, norm compartilhada, colorbars verticais/horizontais, contornos,
hillshade, vetores e layout automático de grids já têm implementações funcionais próprias. A próxima
fundação para elevação/volume 3D exige câmera, projeção de perspectiva,
clipping 3D e depth buffer próprios; não está disponível nesta versão.

Municípios, estradas e bases oficiais detalhadas devem ser distribuídos como
pacotes de dados opcionais com licença e versão explícitas, não como downloads
implícitos ou conteúdo fictício.
