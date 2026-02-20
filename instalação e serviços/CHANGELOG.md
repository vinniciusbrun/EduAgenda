# Changelog - EduAgenda Installer & Services

## [1.0.0] - 2026-02-20

### Criado
- **Controle de Versão Isolado**: O Instalador e os scripts de seviço (Watchdog em background, Parada, Inicialização Automática) agora possuem uma versão independente da versão principal do software. Isso permite atualizar a infraestrutura de background do Windows sem impactar as regras de negócio Web.
- **Botões Numerados (UX)**: A pasta de serviços foi renomeada numericamente para guiar o usuário na ordem lógica de operação: `1 - Iniciar Sistema (Oculto).vbs`, `2 - Parar Sistema.bat` e `3 - Ativar Inicio Automatico.bat`.
- **Botão de Pânico Integrado**: O Instalador agora copia automaticamente o arquivo `2 - Parar Sistema.bat` para dentro da pasta da versão em execução (ex: `vX.Y.Z`). Caso o servidor entre em loop zumbi em background, o usuário não precisará voltar para a pasta original de serviços, possuindo o botão de parada prontamente visível do lado do executável da versão atual.
