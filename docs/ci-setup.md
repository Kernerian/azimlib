# Rodar a CI usando apenas seu Windows

O projeto local ainda não tem repositório remoto. GitHub Actions oferece
[runners Windows, Ubuntu e macOS](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners),
portanto não é necessário instalar três sistemas no computador para executar
os testes automáticos. A matriz preparada tem 24 jobs: 15 de suíte/build/core,
seis do compilador opcional e três de integração Tk.

## Criar e enviar o repositório

1. Entre no GitHub e [crie um repositório](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)
   chamado `azimlib`, privado se preferir. Crie-o vazio: o projeto já inclui
   README, licença e gitignore.
2. Extraia o arquivo `azimlib-github.zip` preparado ao lado da pasta do projeto
   para uma pasta nova. Ela deve conter `pyproject.toml`, `src`, `tests`, `tools`
   e `.github` diretamente na raiz. O ZIP de CI é pequeno porque omite a galeria
   gerada. A distribuição fonte completa conserva os previews offline;
   links de previews na documentação precisam dessa galeria ou de regeneração.
3. Abra PowerShell nessa pasta e execute os comandos abaixo, trocando o URL
   pelo endereço do seu repositório. Git já está disponível no Windows desta
   sessão. A autenticação acontece no fluxo do GitHub/Git Credential Manager.

```powershell
git init
git add .
git commit -m "Initial Azimlib source"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/azimlib.git
git push -u origin main
```

Se o primeiro commit pedir identificação, configure nome/email **nesta pasta**
com `git config user.name "Seu nome"` e `git config user.email "Seu email"`,
e repita o commit. Não é necessário mudar a configuração global do computador.

4. No GitHub, abra **Actions → tests**. O push inicia a matriz. Também há
   `workflow_dispatch` para executar novamente pela interface do GitHub.
5. Ao terminar, conserve a URL da execução e baixe seus artefatos. Cada job
   guarda `result.json`, logs, ambiente/versões, origem instalada e hashes;
   em falha, os logs também são publicados. Use a URL e os artefatos para diagnosticar eventuais falhas.

Nenhum repositório foi criado ou código enviado automaticamente naquele registro histórico.
Uma configuração de workflow não é resultado executado. **5.06 permanece
aberto** até existirem execuções reais das plataformas/versões declaradas.

## CI e conferência física são evidências diferentes

Os smokes desktop usam Tk real com janela retirada e handlers programáticos;
Linux usa Xvfb. Eles verificam contratos, exportação e fechamento, mas não
representam alguém usando mouse/teclado ou avaliando aparência na tela.
O usuário já aceitou a janela Windows nos passos 3/4; **Linux e macOS ainda
precisam de uma conferência direta** para concluir 5.07. Pode ser em máquinas
emprestadas ou com colaboradores que tenham esses sistemas, sem alterar o
escopo da checklist silenciosamente.

Em cada sistema, instalar `.[gui]`, abrir o exemplo de componentes e registrar:
pan e saída/retorno ao canvas, zoom/retângulo, Home/histórico, coordenadas,
resize, Subplots, Salvar PNG/SVG, componentes opcionais e fechamento sem worker
remanescente. Registrar sistema, Python/Tk, DPI, limitações e retorno humano.
Esses resultados devem permanecer separados dos smokes automatizados.

## Repetir localmente

Em um ambiente que já tenha o wheel instalado:

```bash
python -I tools/run_release_checks.py --kind unit --output .ci-results/unit
python -I tools/run_release_checks.py --kind desktop --output .ci-results/desktop
```

Para o kernel opcional, instalar `.[png,accelerate]` e usar `--kind accelerator`.
O runner exige pacote instalado, preserva skips e erros e identifica execução
local como `local`. Não transforma um teste Windows em teste Linux/macOS.
