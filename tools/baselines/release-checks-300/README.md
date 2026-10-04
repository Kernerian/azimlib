# Primeiro runner do lote 5.06–5.09

Snapshot exato usado pelas suítes instaladas Python 3.11/3.14, pelo job do
compilador e pela primeira passagem desktop. Seus hashes permanecem nos JSONs.
As suítes passaram; o layout integrado de seis figuras com exports exatos em
200 DPI ultrapassou o deadline inicial de 300 segundos nos smokes desktop.

O runner atual usa deadline por script de 900 segundos, captura/limpeza da
árvore de subprocessos e permite repetir somente o roteiro que falhou. Essa
mudança é de infraestrutura de validação; não altera o runtime nem relaxa
comparações de pixels/layout. O timeout anterior permanece registrado, não
é apagado nem contado como sucesso. Os resultados de retry são separados.
