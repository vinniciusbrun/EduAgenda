import json
import os
import portalocker
from .security import SecretManager

# Prioriza variável de ambiente (Shared Data) vinda do Orquestrador
DATA_DIR = os.environ.get('EDU_DATA_PATH')

if not DATA_DIR:
    # Fallback para o layout de pasta único (desenvolvimento)
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

class DataManager:
    @staticmethod
    def _get_path(filename):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        return os.path.join(DATA_DIR, filename)

    @staticmethod
    def load(filename):
        path = DataManager._get_path(filename)
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                # portalocker.lock no Windows pode falhar com timeout se usado diretamente assim
                # Vamos simplificar ou usar a forma correta
                portalocker.lock(f, portalocker.LOCK_SH) 
                data = json.load(f)
                portalocker.unlock(f)
                return data
        except portalocker.exceptions.LockException:
            print(f"LOCK ERROR: Tempo esgotado ao tentar ler {filename}")
            return []
        except Exception as e:
            print(f"Erro ao carregar {filename}: {e}")
            return []

    @staticmethod
    def _safe_replace(src, dst):
        import time
        max_retries = 30  
        for i in range(max_retries):
            try:
                # No Windows, as vezes o destino ainda está sendo "soltado" pelo SO 
                # ou por antivírus. Tentamos deletar antes se necessário.
                if os.path.exists(dst):
                    try: os.remove(dst)
                    except: pass
                
                os.rename(src, dst)
                return True
            except (PermissionError, OSError) as e:
                if i == max_retries - 1:
                    print(f"PERM/OS ERROR ({i}): Failed to replace {dst} - {e}")
                    return False
                time.sleep(0.05)  
        return False

    @staticmethod
    def update(filename, callback):
        path = DataManager._get_path(filename)
        temp_path = f"{path}.tmp"
        
        # Se o arquivo não existir, o estado inicial depende do nome/tipo
        # mas por segurança, começaremos com o que callback precisar.
        # Se carregar falhar por falta de arquivo, passaremos None ou empty adequado.
        
        if not os.path.exists(path):
            data = {} if filename == 'config.json' else []
        else:
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except:
                    data = {} if filename == 'config.json' else []
        
        # Lock de leitura/escrita
        # (Nota: O arquivo PRECISA existir para o portalocker funcionar no modo 'r')
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)

        f = open(path, 'r', encoding='utf-8')
        try:
            # Lock exclusivo
            portalocker.lock(f, portalocker.LOCK_EX)
            data = json.load(f)
            new_data = callback(data)
            if new_data is not None:
                with open(temp_path, 'w', encoding='utf-8') as tf:
                    json.dump(new_data, tf, indent=4, ensure_ascii=False)
                
                f.close() 
                DataManager._safe_replace(temp_path, path)
            return new_data
        finally:
            try: f.close() 
            except: pass
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass

    @staticmethod
    def save(filename, data):
        path = DataManager._get_path(filename)
        temp_path = f"{path}.tmp"
        
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        try:
            # Usamos lock para garantir que ninguém esteja lendo/escrevendo no principal
            # enquanto preparamos o temporário
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # Nota: safe_replace aqui pode ser perigoso se não houver um lock global coordenado.
            # Por isso, DataManager.update é PREFERIDO.
            if not DataManager._safe_replace(temp_path, path):
                print(f"ERROR: Could not save {filename} (safe_replace failed)")
                return False
            return True
        finally:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass

def get_professores():
    data = DataManager.load('professores.json')
    if data and isinstance(data, list):
        for i in range(len(data)):
            data[i] = SecretManager.decrypt(data[i])
    return data

def save_professores(data):
    data_to_save = []
    for p in data:
        if isinstance(p, str) and not SecretManager.is_encrypted(p):
            data_to_save.append(SecretManager.encrypt(p))
        else:
            data_to_save.append(p)
    DataManager.save('professores.json', data_to_save)

def get_turmas():
    data = DataManager.load('turmas.json')
    if data and isinstance(data, list):
        for t in data:
            if 'turma' in t: t['turma'] = SecretManager.decrypt(t['turma'])
    return data

def save_turmas(data):
    data_to_save = json.loads(json.dumps(data))
    for t in data_to_save:
        if 'turma' in t and not SecretManager.is_encrypted(t['turma']):
            t['turma'] = SecretManager.encrypt(t['turma'])
    DataManager.save('turmas.json', data_to_save)

def get_agendamentos():
    data = DataManager.load('agendamentos.json')
    if data and isinstance(data, list):
        sensitive = ['professor', 'turma', 'recurso_nome', 'motivo', 'professor_id', 'turma_id']
        for a in data:
            for field in sensitive:
                if field in a: a[field] = SecretManager.decrypt(a[field])
    return data

def save_agendamentos(data):
    data_to_save = json.loads(json.dumps(data))
    sensitive = ['professor', 'turma', 'recurso_nome', 'motivo', 'professor_id', 'turma_id']
    for a in data_to_save:
        for field in sensitive:
            if field in a and not SecretManager.is_encrypted(a[field]):
                a[field] = SecretManager.encrypt(a[field])
    DataManager.save('agendamentos.json', data_to_save)

def update_professores(callback):
    def secure_callback(profs):
        for i in range(len(profs)):
            profs[i] = SecretManager.decrypt(profs[i])
        new_profs = callback(profs)
        if new_profs is not None:
            for i in range(len(new_profs)):
                if isinstance(new_profs[i], str) and not SecretManager.is_encrypted(new_profs[i]):
                    new_profs[i] = SecretManager.encrypt(new_profs[i])
        return new_profs
    return DataManager.update('professores.json', secure_callback)

def update_turmas(callback):
    def secure_callback(turmas):
        for t in turmas:
            if 'turma' in t: t['turma'] = SecretManager.decrypt(t['turma'])
        new_turmas = callback(turmas)
        if new_turmas is not None:
            for t in new_turmas:
                if 'turma' in t and not SecretManager.is_encrypted(t['turma']):
                    t['turma'] = SecretManager.encrypt(t['turma'])
        return new_turmas
    return DataManager.update('turmas.json', secure_callback)

def update_agendamentos(callback):
    def secure_callback(agends):
        sensitive = ['professor', 'turma', 'recurso_nome', 'motivo', 'professor_id', 'turma_id']
        for a in agends:
            for field in sensitive:
                if field in a: a[field] = SecretManager.decrypt(a[field])
        new_agends = callback(agends)
        if new_agends is not None:
            for a in new_agends:
                for field in sensitive:
                    if field in a and not SecretManager.is_encrypted(a[field]):
                        a[field] = SecretManager.encrypt(a[field])
        return new_agends
    return DataManager.update('agendamentos.json', secure_callback)

def get_recursos():
    data = DataManager.load('recursos.json')
    if data and isinstance(data, list):
        for rec in data:
            if 'nome' in rec: rec['nome'] = SecretManager.decrypt(rec['nome'])
    return data

def save_recursos(data):
    def secure_callback(current_recursos):
        data_to_save = json.loads(json.dumps(data))
        for rec in data_to_save:
            if 'nome' in rec and not SecretManager.is_encrypted(rec['nome']):
                rec['nome'] = SecretManager.encrypt(rec['nome'])
        return data_to_save
    
    return DataManager.update('recursos.json', secure_callback)

def update_usuarios(callback):
    def secure_callback(users):
        for user in users:
            if 'username' in user: user['username'] = SecretManager.decrypt(user['username'])
            if 'nome' in user: user['nome'] = SecretManager.decrypt(user['nome'])
            if 'role' in user: user['role'] = SecretManager.decrypt(user['role'])
        
        new_users = callback(users)
        
        if new_users is not None:
            for user in new_users:
                if 'username' in user and not SecretManager.is_encrypted(user['username']):
                    user['username'] = SecretManager.encrypt(user['username'])
                if 'nome' in user and not SecretManager.is_encrypted(user['nome']):
                    user['nome'] = SecretManager.encrypt(user['nome'])
                if 'role' in user and not SecretManager.is_encrypted(user['role']):
                    user['role'] = SecretManager.encrypt(user['role'])
        return new_users
    return DataManager.update('usuarios.json', secure_callback)

def get_usuarios():
    data = DataManager.load('usuarios.json')
    if data and isinstance(data, list):
        for user in data:
            if 'username' in user:
                user['username'] = SecretManager.decrypt(user['username'])
            if 'nome' in user:
                user['nome'] = SecretManager.decrypt(user['nome'])
            if 'role' in user:
                user['role'] = SecretManager.decrypt(user['role'])
    return data

def save_usuarios(data):
    # Cópia profunda simples para evitar mutar o original
    data_to_save = json.loads(json.dumps(data))
    for user in data_to_save:
        if 'username' in user and not SecretManager.is_encrypted(user['username']):
            user['username'] = SecretManager.encrypt(user['username'])
        if 'nome' in user and not SecretManager.is_encrypted(user['nome']):
            user['nome'] = SecretManager.encrypt(user['nome'])
        if 'role' in user and not SecretManager.is_encrypted(user['role']):
            user['role'] = SecretManager.encrypt(user['role'])
    DataManager.save('usuarios.json', data_to_save)

def update_config(callback):
    def secure_callback(cfg):
        # 1. Descriptografar campos sensíveis para o callback trabalhar com dados limpos
        sensitive_fields = [
            'nome_escola', 'coordenador_pedagogico', 
            'github_repo', 'github_user', 'github_token',
            'github_repo_proj', 'github_user_proj', 'github_token_proj'
        ]
        
        for field in sensitive_fields:
            if field in cfg and cfg[field]:
                cfg[field] = SecretManager.decrypt(cfg[field])
        
        if 'project_repos' in cfg:
            for repo in cfg['project_repos']:
                if 'url' in repo: repo['url'] = SecretManager.decrypt(repo['url'])
                if 'token' in repo: repo['token'] = SecretManager.decrypt(repo['token'])

        # 2. Executar a lógica original
        new_cfg = callback(cfg)
        
        if new_cfg is not None:
            # 3. Criptografar novamente antes de salvar no disco
            for field in sensitive_fields:
                if field in new_cfg and new_cfg[field]:
                    if not SecretManager.is_encrypted(new_cfg[field]):
                        new_cfg[field] = SecretManager.encrypt(new_cfg[field])
            
            if 'project_repos' in new_cfg:
                for repo in new_cfg['project_repos']:
                    if 'url' in repo and not SecretManager.is_encrypted(repo['url']):
                        repo['url'] = SecretManager.encrypt(repo['url'])
                    if 'token' in repo and not SecretManager.is_encrypted(repo['token']):
                        repo['token'] = SecretManager.encrypt(repo['token'])
                        
        return new_cfg
        
    return DataManager.update('config.json', secure_callback)

def get_config():
    data = DataManager.load('config.json')
    if not data or isinstance(data, list):
        return {"nome_escola": "EduAgenda", "logo_url": None}
    
    # Lista de campos que devem ser descriptografados automaticamente ao carregar
    sensitive_fields = [
        'nome_escola', 'coordenador_pedagogico', 
        'github_repo', 'github_user', 'github_token',
        'github_repo_proj', 'github_user_proj', 'github_token_proj'
    ]
    
    for field in sensitive_fields:
        if field in data and data[field]:
            data[field] = SecretManager.decrypt(data[field])
            
    # Descriptografar histórico de projetos
    if 'project_repos' in data:
        for repo in data['project_repos']:
            if 'url' in repo: repo['url'] = SecretManager.decrypt(repo['url'])
            if 'token' in repo: repo['token'] = SecretManager.decrypt(repo['token'])
            
    return data

def save_config(data):
    # Lista de campos que devem ser criptografados antes de salvar
    sensitive_fields = [
        'nome_escola', 'coordenador_pedagogico', 
        'github_repo', 'github_user', 'github_token',
        'github_repo_proj', 'github_user_proj', 'github_token_proj'
    ]
    
    # Faz uma cópia para não alterar o objeto original em memória
    data_to_save = data.copy()
    
    for field in sensitive_fields:
        if field in data_to_save and data_to_save[field]:
            # Só criptografa se não estiver criptografado
            if not SecretManager.is_encrypted(data_to_save[field]):
                data_to_save[field] = SecretManager.encrypt(data_to_save[field])
                
    # Criptografar histórico de projetos
    if 'project_repos' in data_to_save:
        for repo in data_to_save['project_repos']:
            if 'url' in repo and not SecretManager.is_encrypted(repo['url']):
                repo['url'] = SecretManager.encrypt(repo['url'])
            if 'token' in repo and not SecretManager.is_encrypted(repo['token']):
                repo['token'] = SecretManager.encrypt(repo['token'])
                
    DataManager.save('config.json', data_to_save)

def get_logs():
    return DataManager.load('logs.json')

def update_logs(callback):
    return DataManager.update('logs.json', callback)
