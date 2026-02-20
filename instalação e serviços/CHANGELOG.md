# Changelog - EduAgenda Installer & Services

## [1.1.0] - 2026-02-20

### Corrigido e Otimizado
- **Prevenção de Infinite Loop (Crash Fatal do Windows)**: O script de instalação original realizava uma cópia da raiz de desenvolvimento (`%~dp0..\*`) injetando silenciosamente o conteúdo inteiro, iterativamente, para dentro de sua própria ramificação `versions\v1.3.13`. Quando os usuários extraíam o pacote sobre a pasta `C:\EduAgenda` e rodavam ali dentro, o `xcopy` ficava em um loop recursivo infinito espelhando pastas como `versions` dentro de `versions`, o que causava congelamento da máquina, memory leak e estouro de estocagem HD. Substituído por `robocopy` parametrizado robusto nativo do OS com flags `/XD` exclusivas de bloqueio, banindo esse colapso por inteiro! 
- **Sincronia de Hot-Swaps Oculta**: Ajustada ramificação estrita do Watchdog Orquestrador (`core/updater.py`) para puxar estritamente o código do endpoint `master` das APIs do GitHub em vez da `main`, sanando falhas de divergências de sincronização que anulavam updates de background automáticos do cliente final.

## [1.0.2] - 2026-02-20

### Corrigido
- **Crash Silencioso no Auto-Start**: Resolvido o defeito onde o sistema recém-instalado "desligava" instantaneamente. O arquivo `1 - Iniciar Sistema (Oculto).vbs` estava bypassando o orquestrador e chamando o `app.py` diretamente, o que o deixava "cego" em relação ao caminho do banco de dados compartilhado. Agora o VBS invoca corretamente o script raiz `run_eduagenda.bat` em modo stealth.
- **Remoção de Hardcode no Runner**: O arquivo central `run_eduagenda.bat` foi atualizado. Ele não exige mais a presença chumbada da versão `v1.2.0` para buscar o interpretador Python inicial. O código agora varre dinamicamente a pasta `versions` em busca do primeiro ambiente virtual funcional.

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
