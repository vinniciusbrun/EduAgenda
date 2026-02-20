# Changelog - EduAgenda

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [1.3.8] - 2026-02-20

### Melhorado
- **Watchdog Fallback (Anti-Crash)**: Implementado um salva-vidas no orquestrador. Se uma atualização recém baixada possuir algum erro fatal que impeça o sistema de rodar (crashando em menos de 15 segundos após o boot), o Watchdog (`manager.py`) detecta a falha, bloqueia e renomeia a versão corrompida (ex: `v2.0_FAILED`), e ressuscita automaticamente a última versão estável conhecida. Isso garante 100% de uptime (disponibilidade) no painel das escolas.

## [1.3.7] - 2026-02-20

### Melhorado
- **Watchdog Updater Diferido**: A lógica de atualização foi aprimorada! Agora, quando um gestor clica em "Atualizar", o sistema apenas *baixa* os arquivos em background e os empacota numa nova versão. O reinício do sistema foi movido para o orquestrador (`manager.py`), que constantemente monitora a pasta de versões.
- **Hot-Swap Silencioso Inteligente**: O orquestrador agora sabe se o servidor Flask está sendo usado ativamente através da nova rota interna `/api/sys/status`. Se uma nova versão for detectada e o sistema estiver ocioso por mais de 3 minutos consecutivos (sem requisições), o orquestrador fará o "Hot-Swap" parando o processo antigo e subindo a nova versão automaticamente.

## [1.3.5] - 2026-02-20

### Melhorado
- **UX do Painel de Configurações**: A aba "Geral" agora é selecionada automaticamente sempre que o modal de configurações é aberto, evitando que o usuário caia em abas secundárias aleatórias do último estado salvo.

## [1.3.4] - 2026-02-20

### Corrigido
- **Inteligência Administrativa (Dashboard BI)**: Resolvido um edge-case severo onde turmas do período Vespertino e Noturno apareciam como IDs brutos (ex: `3A652F14`) caso o Gestor abrisse o Painel de BI logo após o sistema ter pré-carregado um escopo parcial de turmas (Matutino) na tela principal. O Dashboard agora ignora escopos parciais e força o download completo de dicionários ao renderizar relatórios globais.

## [1.3.3] - 2026-02-20

### Corrigido
- **Inteligência Administrativa (Dashboard BI)**: Corrigida a exibição de IDs técnicos (ex: `3A652F14`) nos cartões de Destaque Local, Líder Matutino/Vespertino/Noturno e exportações em Excel. Nomes reais das Turmas e Professores são agora forçados para exibição.
- **Relatório Excel**: Ajustada a função `/api/admin/dashboard/export` para traduzir todos os IDs de turmas e professores utilizando dicionários em tempo real da base de dados.
- **Grid Temporal e Agendamentos**: Resolvido problema onde o Grid ("Visão Semanal") perdia configurações de click (onclick) ao navegar entre semanas, bloqueando os botões inativos/já transcorridos.
- **Permissão de Exclusão (Admin + Professor)**: Permitida a exclusão/edição de slots por professores quando estes são alocados aos horários (campo `professor_id`), garantindo autonomia condicional mesmo se a grade for criada pela coordenação.
- **Tratamento de Erros Server-side**: Captura explícita de `PermissionError` e `ValueError` nos agendamentos, retornando um limpo erro HTTP 403 e 400 em vez de colapsos HTTP 500 no console.
- **Ícones de Cadeado**: Lógica visual do grid e edição readequada – status `locked: true` no banco corretamente amarra a uma identidade trancada na tela (Aberto/Fechado reflete a edição e não a salvação).
- **Travamento de Professor (Segurança)**: O Menu Suspenso de "Professor" no painel principal agora bloqueia qualquer tentativa de um usuário Professor de agendar nome alheio. O Seletor é ancorado (travado) ao ID do login durante o setup de tela.

## [1.3.0] - 2026-02-20
- **Identidade Digital Robusta (UUID)**: Transição de identificação baseada em nomes para IDs únicos universais, garantindo integridade total do histórico de agendamentos.
- **Edição Inline (Click-to-Edit)**: Implementação de correção rápida de nomes para Professores, Turmas e Recursos diretamente nas listas de configurações.
- **Vínculo Identitário**: Professores agora permanecem vinculados aos seus horários e perfis mesmo após alterações em seus nomes de exibição.

### Corrigido
- **Filtro de Professores**: Ajustada a lógica de exibição de professores ativos na agenda para contemplar a nova estrutura de dados.

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
*Gerado por Antigravity AI - v1.3.0 "Identity Core"*
