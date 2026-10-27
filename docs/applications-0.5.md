# Fase E — aplicações Beyond Earth demonstradas

SurfaceFeature separa identifier,kind,Geometry,FeatureName(text,language,authority),
AssetSource,epoch,status,classificação e uncertainty_m opcional. FeatureCatalog
congela o contexto e as feições,limita vértices/arquivos e cria PlanetaryData.
.from_file lê um GeoJSON explicitamente contextualizado,limitado e com SHA-256
obrigatório; não altera o significado terrestre do GeoJSON externo.
.draw reutiliza regiões,paths,símbolos,labels e grupos C/D. Não embute catálogo
IAU,limites geológicos,diâmetros de crateras ou nomes universais nos temas.
Símbolo de cratera marca um ponto, não mede automaticamente o diâmetro.

ExplorationSequence envolve TemporalSeries com contexto,origem/licença,mode,
quantity e unit. Modos observation,reconstruction,visual-interpolation,
simulation,illustrative-plan são declarações do autor; prediction/propagação
operacional são recusados. .bind pre-valida os estados finitos e reutiliza os
Artists existentes,sem criar novos a cada frame. Dados ausentes ocultam a
instância; seleção exact é padrão; nearest/previous são pedidos explícitos,
não extrapolação científica. .animation usa FuncAnimation e seus controles/
exportação existentes. Geometrias temáticas usam graus,campos escalares usam
binders anteriores com seus contratos. Nenhuma efeméride é inferida.

compare_worlds(bodies,mode="physical"|"normalized") cria Figure e Axes comuns
com projeções ortográficas BodySurface explícitas e eixos isolados. physical
usa a mesma escala projetada em metros; normalized ocupa tamanhos visuais
comparáveis e identifica claramente que não é escala física comum. Raios e
unidades aparecem no gráfico. Terreno,perfis e vistas locais podem ser compostos
usando os mesmos Axes/PlanetaryRaster/SurfaceFrame; não há sistema orbital.

## Exemplos

examples/planetary/applications_050.py gera mapas de feições Marte/Lua/Vênus/
Mercúrio,pares Terra-Marte,Marte-Lua,Lua-Mercúrio,Terra-Vênus nos dois modos,
e quatro estados de exploração sintética. DEMs são funções analíticas;
regiões,classificações,nomes e pontos são sintéticos declarados, não observação
ou reconstrução. O atlas marciano D pode reutilizar Viking real já auditado;
a imagem não é elevação medida nem classificação geológica.

## Ciência e pesquisa aberta

Esfera/elipsoide oblato no domínio B: projeção/inversa,distância/azimute/área,
rotas,perfil/terreno e luz geométrica explícita conservam corpus/tolerâncias.
Regiões editoriais angulares e curvas não herdam precisão científica de solver.
Triaxial/irregular,malhas planificadas universais,datum vertical entre missões,
orientação temporal e iluminação astronômica planetária sem dados sustentados
continuam recusados/em pesquisa. Ver surfaces-research-0.5.md; não houve
aproximação esférica silenciosa ou adiamento formal novo.

Evidência adicional necessária: corpus independente por operação/modelo,
restrições de topologia,controle de erro e domínio temporal,licenças de kernels/
datasets fornecidos explicitamente. Dados externos factuais não se tornam
propriedade exclusiva Azimlib. Atmosferas físicas e certificação global de
eclipses continuam fora da implementação demonstrada. A investigação não
bloqueia mapas,símbolos,labels,terreno e observações finitas independentes.
