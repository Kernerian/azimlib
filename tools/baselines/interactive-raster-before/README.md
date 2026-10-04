# Snapshot anterior ao raster temporário de navegação

Código próprio extraído do sdist anterior, antes de sobrescrever a distribuição.
`tk.py` corresponde ao viewer instalado medido em
`docs/pan-responsiveness-before.json`; `pillow.py` corresponde ao renderer
registrado nesse relatório e nos experimentos históricos de stroke kernels.
Os hashes são conferidos na auditoria de distribuição. `_pan_raster.py`
preserva o worker anterior. São referências de desenvolvimento, sem imports
Matplotlib e sem seleção como backend alternativo no pacote instalado.
