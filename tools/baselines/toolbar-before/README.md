# Viewer antes da auditoria da toolbar

smoke_viewer_tk.py preserva o teste anterior de ausência de codecs PNG no viewer,
com hash idêntico ao registrado no relatório municipal histórico. O smoke atual
foi restaurado ao mesmo teste estrito: nenhum codec PNG é usado no viewer,
incluindo os ícones, desenhados diretamente em RGBA. Relatórios históricos
não foram relabelados com o teste/código novo.

Snapshot exato de backends/tk.py antes do ajuste de widgets Pan/Zoom,
overrelief/tamanho físico e ícone Subplots. Preserva o código identificado por
medições históricas de desempenho; não transforma esses resultados antigos
em medições do novo viewer. Apenas desenvolvimento, nunca backend runtime.
