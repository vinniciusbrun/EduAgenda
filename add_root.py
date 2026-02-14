import json
import os
from werkzeug.security import generate_password_hash

USER_FILE = "data/usuarios.json"

def add_root_user():
    if not os.path.exists(USER_FILE):
        print(f"Erro: {USER_FILE} não encontrado.")
        return

    with open(USER_FILE, 'r', encoding='utf-8') as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            print("Erro ao ler JSON de usuários.")
            return

    # Check if root already exists to avoid duplicates
    for user in users:
        if user['username'] == 'root':
            print("Usuário root já existe. Atualizando senha...")
            user['senha'] = generate_password_hash("root")
            user['role'] = "root" # Ensure role is correct
            break
    else:
        print("Criando usuário root...")
        new_user = {
            "username": "root",
            "nome": "Super Usuário (Root)",
            "senha": generate_password_hash("root"),
            "role": "root"
        }
        users.insert(0, new_user) # Add to top

    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)
    
    print("Usuário root configurado com sucesso (Senha: root).")

if __name__ == "__main__":
    add_root_user()
