# Changelog - EduAgenda

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [1.2.0] - 2026-02-20

### Adicionado
- **Arquitetura "Software com Vida"**: Implementação de Orquestrador (`manager.py`) para gestão de ciclo de vida, reinício automático e troca de versões.
- **Isolamento de Versões**: Estrutura de pastas versionadas em `/versions` para atualizações atômicas e seguras.
- **Storage Compartilhado**: Os dados (`/shared/data`) e segredos (`.env`) agora são externos às pastas de versão para persistência total.
- **Ponto de Entrada Robusto**: Novo `run_eduagenda.bat` para iniciar o sistema via Orquestrador.
- **Super Instalador v2.0**: Refatoração completa do `install.bat` com lógica de migração automática para a nova arquitetura.

### Corrigido
- **Upload de Logo**: Restauração completa da funcionalidade de branding (Backend e Frontend) para usuários `admin` e `root`.
- **Suporte Drag-and-Drop**: Implementado arraste de imagens diretamente no header para troca de logo.
- **Cache-Busting v1.2**: Forçado o recarregamento de assets CSS/JS nos navegadores.
- **Segurança de Dependências**: Garantia de instalação limpa em ambientes virtuais (`venv`) isolados.

## [1.1.0] - 2026-02-11

### Adicionado
- **Blindagem de Dados**: Criptografia AES-GCM (SecretManager) em todos os arquivos JSON sensíveis.
- **Backup Satélite**: Sincronização segura para GitHub incluindo backup do arquivo `.env`.
- **Acesso Root**: Refinamento de permissões para o superusuário em todo o sistema.

---
*Gerado por Antigravity AI - v1.2.0 "OLED Ready"*
