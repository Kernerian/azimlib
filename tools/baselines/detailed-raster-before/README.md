# Kernel anterior ao lote 4.08

Snapshot exato dos quatro módulos modificados para compilar opcionalmente os
mesmos cálculos de cobertura e ampliar o orçamento de paths. O benchmark anterior executa o runtime completo
copiado antes do lote, sem importar Numba. Nenhum input externo está neste diretório.

- coverage.py, pillow.py e _render_control.py: hashes completos nos relatórios
  detailed-before. Os bytes deste snapshot resolvem essas referências históricas.
- projected_paths.py: orçamento anterior de 8 MiB, antes do cache atual de 16 MiB.

Para reproduzir a comparação, copie o runtime atual para outro diretório,
substitua estes três módulos no subdiretório azimlib/renderers e remova
_coverage_native.py dessa cópia. Substitua também azimlib/projected_paths.py
pelo snapshot de mesmo nome. Execute benchmark_detailed_map.py apontando
--runtime para o diretório pai do pacote copiado. O caminho novo usa o extra
accelerate; ambos usam o mesmo Python/Pillow e os mesmos dados, não um wrapper.
Confira os hashes antes de comparar. Os dados do IBGE devem ser preparados
separadamente com prepare_original_benchmark.py; não entram nas distribuições.
