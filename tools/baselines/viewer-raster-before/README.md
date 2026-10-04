# Referência própria do viewer antes do buffer direto

Snapshots de código da Azimlib, imediatamente antes de separar render_image
de render_png e remover o round-trip PNG/cópia da primeira imagem no Tk.
Não são código Matplotlib nem fazem parte do runtime/wheel.

benchmark_viewer.py importa ambos os caminhos em cada processo novo,
seleciona um e compara pixels/estados de sete etapas. O renderer/geometrias,
fontes, AA, redução BOX e código de cobertura permanecem equivalentes;
a saída do snapshot PNG também é confrontada em test_raster_image.py.

O baseline tem a mesma licença de software da Azimlib. Não o atualize para
acompanhar alterações futuras: serve para regressão reproduzível deste lote.
