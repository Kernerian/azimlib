# Dados geográficos incluídos

Azimlib distribui um pequeno catálogo **offline** de dados reais do
[Natural Earth](https://www.naturalearthdata.com/). A biblioteca não baixa dados
durante importação, renderização ou exportação.

| Camada | Cobertura | Escala de origem | Feições |
| --- | --- | --- | ---: |
| `countries` | Mundo | 1:110.000.000 | 177 |
| `brazil` | Brasil, contorno nacional detalhado | 1:10.000.000 | 1 |
| `states` | 26 estados do Brasil e Distrito Federal | 1:10.000.000 | 27 |
| `rivers` | Principais rios e eixos de lagos, mundo | 1:50.000.000 | 461 |
| `lakes` | Principais lagos, mundo | 1:50.000.000 | 412 |
| `coastlines` | Costas, mundo | 1:50.000.000 | 1.428 |

Os seis arquivos comprimidos ocupam aproximadamente 1,3 MB. Seus vértices
originais são preservados e arredondados para cinco casas decimais em graus;
o arredondamento não aumenta a precisão cartográfica dos dados de origem.
As propriedades selecionadas usam nomes em minúsculas. Todos os dados usam
longitude e latitude WGS 84, nesta ordem, em graus.
Uma feição vazia de rio (Loire, sem coordenadas no arquivo de origem) foi
omitida; o manifesto registra a quantidade de geometrias vazias excluídas.

```python
from azimlib import datasets

brasil = datasets.country("Brasil")   # também "brazil", "BR", "BRA"
franca = datasets.country("France")   # nomes em inglês/português e códigos ISO
estados = datasets.load("states")
rios = datasets.load("rivers", country="BR")
fontes = datasets.provenance()
catalogo = datasets.catalog()
```

Cada chamada retorna um dicionário GeoJSON independente. Alterá-lo não muda os
próximos carregamentos. `country("world")` fornece os países a 1:110 milhões;
`country("Brazil")` usa o contorno brasileiro a 1:10 milhões. Por isso, um mapa
mundial e um mapa detalhado do Brasil têm níveis de generalização diferentes.

O filtro `country` de rios, lagos e costas é uma **seleção por retângulo
envolvente**, sem recortar as geometrias na fronteira política. Uma feição que
cruza esse retângulo pode continuar para outro país. A janela do mapa faz seu
próprio recorte visual. Países com territórios distantes ou que atravessam o
antimeridiano podem selecionar áreas muito amplas.

## Limites de uso e interpretação

Estes dados são generalizados para cartografia em escalas pequenas. Não servem
para navegação, cadastro, limites legais ou análise de precisão. O catálogo não
é um inventário completo de rios, lagos, ilhas ou territórios. Municípios,
estradas, altimetria e divisões administrativas de outros países ainda precisam
ser fornecidos pelo usuário em GeoJSON. Solicitar estados de outro país produz
um erro explícito, sem inventar dados nem retornar estados brasileiros.

As feições seguem as decisões cartográficas do Natural Earth, inclusive seu
[tratamento de fronteiras disputadas](https://www.naturalearthdata.com/about/).
Dados populacionais de países conservam o campo `pop_year`; não representam
necessariamente a população atual. Não há classificação de navegabilidade de
rios neste catálogo: espessuras e estilos atribuídos em exemplos são escolhas
visuais e não certificam trechos navegáveis.

## Licença e reprodução

O Natural Earth declara seus dados vetoriais e raster em domínio público e
permite redistribuição e modificação. Veja os
[termos oficiais](https://www.naturalearthdata.com/about/terms-of-use/).
A atribuição sugerida é “Made with Natural Earth.” Os dados não têm a licença
de software da biblioteca; sua condição de domínio público é independente.

O arquivo `src/azimlib/data/manifest.json` registra os URLs imutáveis,
o commit `ca96624a56bd078437bca8184e78163e5039ad19` do repositório de origem,
hashes SHA-256 dos downloads e dos arquivos distribuídos, cobertura, escala e
processamento aplicado. Não existe simplificação por uma biblioteca geoespacial
nem geração de polígonos fictícios.

Para reconstruir os dados, execute na raiz do projeto:

```console
python tools/fetch_data.py --cache ../../work/natural-earth
```

Esse comando de manutenção requer internet e usa apenas a biblioteca padrão de
Python. Downloads intermediários ficam no diretório `--cache`. A reconstrução
usa versão fixa, retém todos os vértices, normaliza propriedades, filtra o Brasil
nas duas camadas detalhadas e produz gzip com timestamp zero. A sequência
comprimida pode variar entre versões de zlib; o manifesto registra o resultado
efetivamente produzido.
