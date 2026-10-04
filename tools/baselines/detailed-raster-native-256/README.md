# Primeira configuração do compilador opcional

Snapshot exato de pillow.py usado nos relatórios detailed-after-*-r*.json.
O kernel nativo já compilava os nossos cálculos, mas só era ativado em runs
com 256 pontos ou mais. A configuração seguinte inclui runs de 32 pontos,
como os contornos dos marcadores. Os resultados finais recebem prefixo
detailed-final; os relatórios anteriores não são renomeados nem relabelados.
O projected_paths.py daquele experimento corresponde ao snapshot preservado
em detailed-raster-before (orçamento de 8 MiB). Os demais módulos registrados
podem ser resolvidos pelos hashes do runtime atual e dos baselines.
