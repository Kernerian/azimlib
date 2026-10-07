# Inventário das frentes após a 0.2.0

A 0.2.0 está publicada e sua checklist encerrou 54/54 itens. A implementação
posterior segue a [checklist operacional da 0.3.0](release-progress-0.3.md).
As 16 frentes abaixo são categorias, não a contagem de tarefas faltantes.

| Frente anterior | Passos 0.3.0 | Trabalho do próximo corte |
| --- | --- | --- |
| 1. Visual e exportação | 6, 10 | Raster/subpixel, PDF e baselines. |
| 2. Axis/ticks/escalas/unidades | 3, 4 | Unidades, formatos, datas e bordas curvas. |
| 3. Layout | 4 | Corte implementado: SubFigure, raízes disjuntas e compressed limitado; [contratos](transforms-composition.md). |
| 4. Artists/API | 4, 5 | Transforms, gaps e Paths implementados; contourf permanece no passo 5. |
| 5. Transforms | 3, 4, 8 | Composição/inversas/unidades implementadas; câmera no passo 8. |
| 6. Legendas/colorbars | 4, 5, 9 | Handlers, máscaras, classes e vínculo temporal. |
| 7. Labels/texto | 6 | Âncoras, curvas, colisões e tipografia. |
| 8. Estilos/símbolos/coleções | 1, 4, 6 | Ciclos, regras, ícones/padrões próprios ou licenciados. |
| 9. Interação/widgets | 7, 9 | Picking, seletores, sliders e plataformas. |
| 10. Backends/integração | 7 | Qt próprio, notebook e Python/viewer portátil. |
| 11. Desempenho | 7, 10 | Simplificação, caches e medição urbana/densa. |
| 12. Robustez cartográfica | 3 | Fundação concluída no corte regional: elipsoide, UTM, antimeridiano e topologia básica; [limites](geodesy.md). |
| 13. Formatos/dados/urbano | 1, 2 | Fundação concluída: CSV, Shapefile/DBF, KML, OSM XML e georreferência; extensões nos passos seguintes. |
| 14. Raster/terreno/ciência | 5 | RGB/NoData/resampling, campos, contornos e fluxos. |
| 15. 3D/tempo | 8, 9 | Terreno/extrusão CPU e animação/atlas. |
| 16. Docs/testes/distribuição | 10 | Galeria, CI, proveniência e instalação/release gates. |

A contagem de concluídos/pendentes fica somente na checklist. As reservas
para 0.4.0 estão ali motivadas: volumes/GPU, PBF planetário, CRS com grids
universais, overlay global, roteamento/geocodificação e TeX/shaping completos.
O restante não desaparece do plano. Novos recursos ainda pendentes não são
capabilidades anunciadas da versão 0.2.0.
