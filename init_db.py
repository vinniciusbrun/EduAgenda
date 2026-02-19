import os
import sys
from werkzeug.security import generate_password_hash
from core.models import get_usuarios, save_usuarios

def init_db():
    print("[*] Inicializando base de usuários administrativos...")
    
    try:
        usuarios = get_usuarios()
        changed = False

        # 1. Garantir Usuário Root
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

        # 2. Garantir Usuário Admin
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
