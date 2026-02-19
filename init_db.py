import os
import sys
import json
from werkzeug.security import generate_password_hash
from core.models import get_usuarios, save_usuarios, get_config, save_config

def init_db():
    print("[*] Inicializando base de dados e usuários...")
    
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # 1. Garantir Estrutura dos Arquivos JSON
    files_to_init = {
        'config.json': {},
        'professores.json': [],
        'turmas.json': [],
        'agendamentos.json': [],
        'recursos.json': [],
        'logs.json': [],
        'usuarios.json': []
    }

    for filename, default_content in files_to_init.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            print(f"[+] Criando arquivo {filename}...")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, indent=4, ensure_ascii=False)
        else:
            # Se o arquivo existe mas está vazio ou inválido para o tipo esperado
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                
                # Correção estrutural se config.json for uma lista (bug anterior)
                if filename == 'config.json' and isinstance(content, list):
                    print(f"[!] Corrigindo estrutura de {filename} (Lista -> Objeto)...")
                    save_config({"nome_escola": "EduAgenda", "logo_url": None})
            except (json.JSONDecodeError, ValueError):
                print(f"[!] Resetando arquivo corrompido: {filename}...")
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f, indent=4, ensure_ascii=False)

    try:
        usuarios = get_usuarios()
        changed = False

        # 2. Garantir Usuário Root
        root_exists = any(u['username'] == 'root' for u in usuarios)
        if not root_exists:
            print("[+] Criando usuário ROOT padrão...")
            usuarios.insert(0, {
                "username": "root",
                "nome": "Super Usuário (Root)",
                "senha": generate_password_hash("root"),
                "role": "root",
                "active": True
            })
            changed = True
        else:
            # Garante que a role esteja correta (migração legada)
            for u in usuarios:
                if u['username'] == 'root' and u.get('role') != 'root':
                    print("[!] Corrigindo role do ROOT para soberania total...")
                    u['role'] = 'root'
                    changed = True

        # 3. Garantir Usuário Admin
        admin_exists = any(u['username'] == 'admin' for u in usuarios)
        if not admin_exists:
            print("[+] Criando usuário ADMIN padrão...")
            usuarios.append({
                "username": "admin",
                "nome": "Administrador",
                "senha": generate_password_hash("admin"),
                "role": "admin",
                "active": True
            })
            changed = True

        if changed:
            save_usuarios(usuarios)
            print("[OK] Base de usuários atualizada com sucesso.")
        else:
            print("[i] Usuários administrativos já configurados.")

    except Exception as e:
        print(f"[X] Erro ao inicializar banco de dados: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
