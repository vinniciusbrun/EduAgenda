# Agenda de Recursos Pedagógicos

Sistema completo para gestão e agendamento de recursos escolares (Chromebooks, Laboratórios, Tablets), desenvolvido em Python com Flask.

![Status](https://img.shields.io/badge/status-stable-green)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-orange)

## 📋 Sobre o Projeto

O **Agenda de Recursos** foi criado para facilitar a organização de recursos pedagógicos em instituições de ensino. O sistema permite que professores agendem equipamentos e espaços, enquanto a coordenação tem uma visão completa do uso através de um Dashboard BI.

### ✨ Principais Recursos

- **Agendamento Inteligente**: Prevenção de conflitos de horário e validação de regras de negócio.
- **Gestão de Turmas e Professores**: Cadastro simplificado via planilhas Excel ou interface web.
- **Dashboard BI**: Gráficos interativos para análise de dados e ocupação de recursos.
- **Controle de Acesso**: Níveis de permissão diferenciados (Visualização, Professor, Admin, Root).
- **Backup em Nuvem**: Integração nativa com GitHub para versionamento e backup automático dos dados.
- **Modo Quiosque/Laptop**: Interface responsiva e otimizada para diferentes dispositivos.
- **Logs e Auditoria**: Rastreamento detalhado de ações críticas no sistema.

## 🛠️ Tecnologias e Bibliotecas

O sistema foi construído sobre uma base sólida de tecnologias open-source:

- **Core**: `Python 3.9+`
- **Web Framework**: `Flask 3.0`
- **Manipulação de Dados**: `Pandas 2.1`, `OpenPyXL`
- **Servidor de Produção**: `Waitress`
- **Agendamento de Tarefas**: `APScheduler`
- **Concorrência**: `Portalocker` (para garantir integridade de arquivos)
- **Frontend**: HTML5, CSS3 (Glassmorphism), JavaScript Vanilla

## ⚙️ Pré-requisitos

Para rodar o sistema, você precisará de:

1.  **Python 3.9** ou superior.
2.  **Git** instalado e configurado (para funcionalidades de backup).
3.  Sistema Operacional: Windows 10/11 (recomendado para os scripts de automação), Linux ou macOS.

## 🚀 Instalação e Execução

Siga os passos abaixo para colocar o sistema no ar:

1.  **Clone o repositório**:
    ```bash
    git clone https://github.com/seu-usuario/seu-repo.git
    cd seu-repo
    ```

2.  **Instalação Automática (Windows)**:
    - Navegue até a pasta `instalação e serviços`.
    - Execute o arquivo `install.bat` como administrador.
    - O script criará o ambiente virtual e instalará todas as dependências.

3.  **Iniciar o Servidor**:
    - Na pasta `instalação e serviços`, execute `start_hidden.vbs` para rodar em segundo plano (sem janela preta).
    - Ou rode `python app.py` na raiz para ver os logs no terminal.

4.  **Acesso e Rede**:
    - Para que o sistema funcione na rede interna, **configure um IP Fixo** nesta máquina servidora.
    - Acesse localmente: `http://localhost:5000`
    - Acesse de outros computadores: `http://SEU-IP-FIXO:5000` (ex: `http://192.168.1.10:5000`)
    - **Importante**: Certifique-se de liberar a porta **5000** no Firewall do Windows.

## 📂 Estrutura de Serviços

Na pasta `instalação e serviços` você encontra utilitários para facilitar a gestão:

- `install.bat`: Instala dependências e configura o ambiente.
- `start_hidden.vbs`: Inicia o sistema de forma silenciosa.
- `parar_sistema.bat`: Encerra o servidor com segurança.
- `ativar_inicio_automatico.bat`: Configura o Windows para iniciar o sistema junto com o PC.

## 📄 Licença e Créditos

Este projeto é **Open Source** sob a licença MIT, com a adição da cláusula de atribuição.

**Você é livre para:**
- Usar, copiar, modificar, mesclar, publicar, distribuir, sublicenciar e/ou vender cópias do Software.

**Sob as seguintes condições:**
1.  **Crédito Obrigatório**: O aviso de direitos autorais acima e este aviso de permissão devem ser incluídos em todas as cópias ou partes substanciais do Software.
2.  **Autoria**: Deve-se dar o devido crédito ao criador original do sistema em qualquer documentação ou interface pública derivada deste trabalho.

---
*Desenvolvido com foco em eficiência e usabilidade.*
