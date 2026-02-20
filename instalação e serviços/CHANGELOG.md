# Changelog - EduAgenda Installer & Services

## [1.0.1] - 2026-02-20

### Corrigido e Melhorado
- **Encoding de Caracteres Especiais**: O script do instalador agora força nativamente a página de códigos UTF-8 (`chcp 65001`) no prompt de comando do Windows. Isso corrige um bug crítico onde a instalação abortava no final com o erro "O sistema não encontrou o arquivo" ao tentar abrir a pasta "instalação e serviços" em SOs de linguagens diferentes.
- **Root Padronizado**: O prompt iterativo foi removido. Agora a instalação obrigatoriamente força a raiz como `C:\EduAgenda`, padronizando o ambiente e reduzindo atrito para o usuário.

## [1.0.0] - 2026-02-20

### Criado
- **Controle de Versão Isolado**: O Instalador e os scripts de seviço (Watchdog em background, Parada, Inicialização Automática) agora possuem uma versão independente da versão principal do software. Isso permite atualizar a infraestrutura de background do Windows sem impactar as regras de negócio Web.
- **Botões Numerados (UX)**: A pasta de serviços foi renomeada numericamente para guiar o usuário na ordem lógica de operação: `1 - Iniciar Sistema (Oculto).vbs`, `2 - Parar Sistema.bat` e `3 - Ativar Inicio Automatico.bat`.
- **Botão de Pânico Integrado**: O Instalador agora copia automaticamente o arquivo `2 - Parar Sistema.bat` para dentro da pasta da versão em execução (ex: `vX.Y.Z`). Caso o servidor entre em loop zumbi em background, o usuário não precisará voltar para a pasta original de serviços, possuindo o botão de parada prontamente visível do lado do executável da versão atual.
- **Auto-Run Pós Instalação**: O script `install.bat` agora dispara o servidor oculto e abre o navegador automaticamente na porta local assim que o processo de inicialização e extração for concluído (primeira instalação da máquina).
