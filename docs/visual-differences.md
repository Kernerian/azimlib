# Diferenças visuais e comportamentais registradas

Referência de desenvolvimento: Matplotlib 3.11.2/Agg, Python 3.14.4, Windows.
Azimlib permanece independente; o renderer cartográfico, Scene, layout e API
são próprios. Este registro encerra **3.09**, após a
[conferência 3.08 da janela Tk visível no Windows](viewer-visible-acceptance.md).

| Área | Diferença / limite atual | Evidência e decisão |
|---|---|---|
| Texto raster | Agg usa hinting/posições de glifos; Azimlib usa cobertura/supersampling próprios com Pillow | [Qualidade](image-quality.md), [fontes e rotação](text-rotation.md); não se promete identidade dos pixels. Máxima diferença das caixas nas 768 referências de rotação: cerca de 1,43 px a 100 DPI |
| Traços e clipping | Cobertura subpixel, recorte fracionário, caps/joins/dashes podem rasterizar diferentemente | [Estilos](style-quality.md), [mapas completos](complete-map-quality.md) e [baselines atuais](release-gallery.md); larguras públicas continuam em pontos |
| Hachuras | Vocabulário e repetição familiares; formas/espacamento gerados pelo nosso núcleo | [Científico](scientific.md); comparar o mesmo Scene em Agg não compara o gerador nativo de hachuras |
| SVG | Texto vetorial editável com fontes DejaVu embarcadas; rasterização final depende do viewer | [Renderers](architecture.md); XML/textos/clip/transform conferidos, sem alegar PNG idêntico em todos os navegadores |
| Layout | Solver próprio por medidas, uma raiz GridSpec e seus filhos; projeção preserva aspecto geográfico | [Aceite de layout](layout-acceptance.md); posições manuais e textos livres continuam responsabilidade do autor |
| Colorbar no topo | A referência Tk/Agg usa posicionamento por baseline no rótulo superior; gap visível pode diferir do labelpad | [24 controles/18 gaps físicos](layout-acceptance-reference.json); nos casos registrados, Azimlib mantém 8 pt de distância geométrica, referência superior aproximadamente 4,64 pt |
| Isolinhas | Marching squares, decisões em saddles e posicionamento de labels próprios | [Limites de contornos](contour-boundaries.md), [edições](lines-contours.md); sem contourf, triangulação ou toda a política automática de clabel |
| Componentes cartográficos | Escala, norte, rosa e overview são extensões opt-in; não são componentes nativos do pyplot | [Componentes](components.md); norte/rosa independentes, foco preto e escala local esférica |
| Dados/projeções no corte 0.2.0 | Natural Earth generalizado, seis projeções esféricas; transformação 4326/3857 própria | [Dados](data.md), [matemática](math.md); diferenças de datum/elipsoide/detalhe não são defeitos do renderer |
| Viewer Tk | Renderer/navegação e sete ícones próprios, sem assets/código da referência. Grupos de botões e tooltip imediato à direita seguem Tk; Pan/Zoom são Checkbuttons. Pan altera limites e redesenha ticks durante o arrasto, sem traduzir bitmap/moldura. Hover plano, editor ttk e nomes opcionais preservados | [Quatro escalas Tk](toolbar.md), [60 gestos e integração](pan-interaction.md), [verificação visual Windows](viewer-visible-acceptance.md); decoração Tk não é Qt. Aparência/input observados neste Windows aceitos em 3.08; latência/input Windows encerrados em [4.09](performance-acceptance.md); [CI desktop nos três sistemas](ci-0.2.0.json) aprovada. Conferência humana nativa Linux/macOS fica posterior, conforme o [aceite 0.2.0](release-acceptance.md) |
| Viewer HTML | Cena offline sem vínculo com Python; navegação/ornamentos dependem da projeção | [Navegação](portable-navigation.md), [componentes](components.md); não se declara equivalência integral ao desktop |

O [catálogo da galeria](release-gallery.md) separa referências nativas de
comparações de raster sobre a mesma cena. Os JSON antigos de desempenho e
qualidade preservam os hashes/medições do código que produziram seus resultados;
as novas baselines têm relatório próprio. As métricas RGB são diagnósticos,
não notas de qualidade perceptual.

Correções de geometria, textos e componentes já auditadas estão nos aceites
[1](artist-acceptance.md) e [2](layout-acceptance.md). Este registro não converte
uma verificação oculta em inspeção da janela visível. O passo 3 foi encerrado
com observação visual Windows, além dos testes/artefatos; a medição física
Windows e a CI nos três sistemas encerraram os passos 4–5. A conferência humana
nativa Linux/macOS permanece uma limitação documentada do corte 0.2.0.

A 0.3.0 em desenvolvimento acrescenta duas projeções esféricas, TM/UTM
elipsoidais regionais, geodesia e vistas cruzadas. Esse avanço possui
[matriz numérica e limites próprios](geodesy.md); não altera retroativamente
as medições visuais da 0.2.0 descritas acima.
