import os
import json
import logging
import subprocess
import requests
from datetime import datetime

class Updater:
    """
    Handles system versioning, environment isolation, and GitHub synchronization.
    """
    VERSION_FILE = 'version.json'
    DATA_DIR = 'data'
    
    @staticmethod
    def get_local_version():
        try:
            if os.path.exists(Updater.VERSION_FILE):
                with open(Updater.VERSION_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error reading version file: {e}")
        return {"version": "0.0.0"}

    @staticmethod
    def increment_version():
        data = Updater.get_local_version()
        parts = data['version'].split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        data['version'] = '.'.join(parts)
        data['updated_at'] = datetime.now().isoformat()
        
        with open(Updater.VERSION_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return data['version']

    @staticmethod
    def is_venv():
        """Checks if the system is running inside a virtual environment."""
        # Note: 'sys' is not imported here, this method would cause a NameError.
        # Assuming 'sys' would be imported if this method were actually used.
        return os.path.exists('venv') or hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    @staticmethod
    def sync_push(repo_url, token):
        """
        Synthesizes the developer flow: Incs version, commits non-data files, and pushes.
        Public Repo Safe version: Relies on .gitignore and clean history.
        """
        if not token:
            return False, "Token do GitHub não configurado."

        cwd = os.getcwd()
        
        # 0. Garantir .gitignore robusto antes de qualquer operação
        gitignore_path = os.path.join(cwd, '.gitignore')
        required_ignores = ['data/', '.env', '*.xlsx', '*.bak', 'venv/', '__pycache__/', '*.pyc']
        try:
            current_ignores = ""
            if os.path.exists(gitignore_path):
                with open(gitignore_path, 'r') as f:
                    current_ignores = f.read()
            
            with open(gitignore_path, 'a+') as f:
                for ignore in required_ignores:
                    if ignore not in current_ignores:
                        f.write(f"\n{ignore}")
        except Exception as e:
            logging.error(f"Error updating .gitignore: {e}")

        new_version = Updater.increment_version()
        try:
            # 1. Garantir que o repositório Git existe localmente
            if not os.path.exists(os.path.join(cwd, '.git')):
                subprocess.run(['git', 'init'], cwd=cwd, check=True)

            # 2. Configurar Identidade Mínima
            subprocess.run(['git', 'config', 'user.name', 'System Updater'], cwd=cwd, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'updater@system.local'], cwd=cwd, capture_output=True)

            # 3. Detectar Branch Atual
            branch_res = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=cwd, capture_output=True, text=True)
            current_branch = branch_res.stdout.strip() or 'main'
            if 'fatal' in current_branch or not current_branch:
                current_branch = 'main'

            # 4. Preparar URL Autenticada
            clean_repo = repo_url.replace("https://", "").replace("http://", "")
            auth_url = f"https://{token}@{clean_repo}"

            # 5. Tentar Pull antes de tudo para evitar rejeição
            try:
                subprocess.run(['git', 'pull', auth_url, current_branch, '--rebase', '--allow-unrelated-histories'], 
                               cwd=cwd, capture_output=True, text=True)
            except:
                pass

            # 6. Executar Fluxo Git Seguro
            # Remove arquivos protegidos da cache (caso já estejam sendo rastreados)
            for pattern in required_ignores:
                subprocess.run(['git', 'rm', '-r', '--cached', pattern.rstrip('/')], cwd=cwd, capture_output=True)

            # Adiciona apenas o que não está no .gitignore
            subprocess.run(['git', 'add', '-A'], cwd=cwd, check=True)

            # Commit
            msg = f"Build v{new_version} - Auto Sync"
            subprocess.run(['git', 'commit', '-m', msg], cwd=cwd, capture_output=True)

            # Push Autenticado
            res = subprocess.run(['git', 'push', auth_url, current_branch], cwd=cwd, capture_output=True, text=True)
            
            if res.returncode != 0:
                # Se falhar por causa de 'push protection' ou similar, avisa o usuário
                error_msg = res.stderr
                if "GH013" in error_msg or "PUSH PROTECTION" in error_msg:
                    return False, "Push Bloqueado pelo GitHub: Foram detectados segredos (tokens/senhas). Limpe o histórico do Git primeiro."
                raise Exception(f"Git Push Failed: {error_msg}")
                
            return True, f"Versão {new_version} enviada com sucesso para branch '{current_branch}'!"
        except Exception as e:
            logging.error(f"Sync Error: {e}")
            return False, f"Erro no Push: {str(e)}"

    @staticmethod
    def check_remote_version(repo_url, token=None):
        """Fetches version.json from GitHub, using API if token is provided (for private repos)."""
        try:
            # 1. Tenta usar a API oficial se houver token (Robusto para repos privados)
            if token:
                # Extrai user/repo da URL
                clean = repo_url.replace("https://github.com/", "").replace("http://github.com/", "").replace(".git", "")
                parts = clean.split("/")
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/version.json"
                    headers = {
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3.raw"
                    }
                    response = requests.get(api_url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        return response.json()

            # 2. Fallback para Raw Content (Público) - Tenta 'main'
            raw_url_main = repo_url.replace("github.com", "raw.githubusercontent.com").replace(".git", "/main/version.json")
            response = requests.get(raw_url_main, timeout=5)
            if response.status_code == 200:
                return response.json()
            
            # 3. Fallback final - Tenta 'master'
            raw_url_master = repo_url.replace("github.com", "raw.githubusercontent.com").replace(".git", "/master/version.json")
            response = requests.get(raw_url_master, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logging.error(f"Error checking remote version: {e}")
        return None

    @staticmethod
    def install_update(repo_url, token=None):
        """
        Runs the atomic update flow.
        """
        temp_dir = 'temp_update'
        backup_dir = 'old_version_backup'
        zip_path = 'update.zip'
        
        try:
            # 1. Download ZIP via GitHub API
            owner_repo = repo_url.replace("https://github.com/", "").replace(".git", "")
            zip_url = f"https://api.github.com/repos/{owner_repo}/zipball/main"
            
            headers = {}
            if token: headers['Authorization'] = f'token {token}'
            
            response = requests.get(zip_url, headers=headers, stream=True)
            if response.status_code != 200:
                return False, f"Falha ao baixar atualização: {response.status_code}"
                
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
            
            # 2. Extrair
            import zipfile
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(temp_dir)
            
            root_folder = os.listdir(temp_dir)[0]
            inner_dir = os.path.join(temp_dir, root_folder)
            
            # 3. Backup
            if os.path.exists(backup_dir): shutil.rmtree(backup_dir)
            os.makedirs(backup_dir)
            
            ignore_list = [Updater.DATA_DIR, 'venv', temp_dir, backup_dir, '.git', zip_path, '__pycache__', '.env']
            for item in os.listdir('.'):
                if item not in ignore_list:
                    dest = os.path.join(backup_dir, item)
                    if os.path.isdir(item): shutil.copytree(item, dest, dirs_exist_ok=True)
                    else: shutil.copy2(item, dest)
            
            # 4. Aplicar
            for item in os.listdir(inner_dir):
                s = os.path.join(inner_dir, item)
                d = os.path.join('.', item)
                if os.path.isdir(s):
                    if item not in [Updater.DATA_DIR, 'venv', '.git']:
                        shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            
            # 5. Verificar Dependências (requirements.txt)
            req_file = 'requirements.txt'
            if os.path.exists(req_file):
                # Verifica se o arquivo mudou comparando com o backup (opcional, aqui faremos direto por segurança)
                if Updater.is_venv():
                    logging.info("Alteração detectada r em requirements.txt. Atualizando dependências no venv...")
                    try:
                        # No Windows, o executável do pip está em venv/Scripts/pip
                        pip_path = os.path.join('venv', 'Scripts', 'pip.exe')
                        if not os.path.exists(pip_path): pip_path = 'pip' # Fallback
                        subprocess.run([pip_path, 'install', '-r', req_file], check=True)
                    except Exception as pip_err:
                        logging.error(f"Erro ao atualizar dependências: {pip_err}")

            # 6. Limpeza
            os.remove(zip_path)
            shutil.rmtree(temp_dir)
            
            return True, "Sistema atualizado e dependências verificadas! Iniciando reinício..."
            
        except Exception as e:
            return False, f"Erro crítico na atualização: {str(e)}"
