# Revisão humana 7.08 — tipografia internacional

O item **7.08 permanece pendente** até haver aceite explícito em Windows,
Linux e macOS. Gerar arquivos ou passar testes não substitui essa inspeção.
O workflow manual `text-review-0.4.yml` prepara três artifacts independentes:
`azimlib-0.4-complex-text-windows`, `azimlib-0.4-complex-text-linux` e
`azimlib-0.4-complex-text-macos`. Não publica documentação ou pacotes.

## Arquivos a comparar

Abra `index.html` de cada artifact, mantendo as três pastas separadas.
Compare arquivos de mesmo nome, em tamanho natural, com o mesmo visualizador.
`manifest.json` registra fontes fixadas, versões dos motores, hashes das saídas
e do código. Exija o mesmo código e fontes nas três plataformas. Os hashes dos
PNG não precisam ser iguais entre sistemas; investigue diferenças visuais.

| Arquivo | Verificação |
| --- | --- |
| `specimens.png`, `.svg`, `.pdf` | Acentos compostos, ligaturas, conexão árabe, números/pontuação em RTL/LTR, devanágari e cobertura CJK |
| `multilingual-map-100dpi.*` | Labels, título, eixos, legenda, colorbar e texto sobre curva sem cortes ou colisões inesperadas |
| `multilingual-map-200dpi.*` | Mesmo tamanho físico, contornos nítidos, rotações e espaçamentos consistentes |
| `multilingual-map.html` | Abertura offline, textos e controles; conferir limites documentados da recomposição no navegador |
| `tk-multilingual-native.png`, `qt-multilingual-native.png` | Canvas do aplicativo correto, texto, toolbar, escala do sistema e margens |
| `unicode-conformance.json`, `licenses.json`, `source-privacy.json` | Execução completa aprovada e avisos preservados |

As referências são saídas da própria Azimlib. Não são renderizações de outra
biblioteca. Capturas estáticas não medem fluidez: em uma sessão interativa de
cada sistema, confira pan, zoom, Home, redimensionamento e edição de texto.
O runner Linux usa Xvfb com plugin Qt nativo XCB; isso não comprova todas as
combinações de compositor/monitor de um desktop Linux real.

## Checklist de aceite por sistema

- [ ] Windows: PNG/SVG/PDF, scripts, rotações/DPI e Tk/Qt conferidos.
- [ ] Linux: PNG/SVG/PDF, scripts, rotações/DPI e Tk/Qt conferidos.
- [ ] macOS: PNG/SVG/PDF, scripts, rotações/DPI e Tk/Qt conferidos.
- [ ] Identificador da execução, commit/hashes de origem e observações registrados.
- [ ] Aceite humano explícito dos três sistemas registrado no item 7.08.

Para preparar localmente, instale os extras `text,gui,qt`, adquira as fontes
explicitamente e use um diretório de saída novo:

```bash
python -I tools/acquire_text_fonts.py --output .text-fonts
python -I tools/validate_text_engine.py --fonts .text-fonts --output text-review --native
```

O gerador inclui este roteiro no pacote. Não captura o desktop arbitrariamente:
Tk verifica o canvas antes de salvar e Qt captura sua própria janela.

Antes da inspeção, a ferramenta abaixo confere hashes, capturas nativas e a
mesma origem/fontes nos três pacotes. Ela **nunca registra aceite humano**:

```bash
python -I tools/compare_text_review.py --packet windows --packet linux --packet macos --report comparison.json
```
