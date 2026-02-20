import os
import json
import logging
import subprocess
import requests
import sys
import shutil
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
    def sync_push(repo_url, token, force=False):
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

            # 5. Tentar Pull antes de tudo para evitar rejeição (se não for forçado)
            if not force:
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
            push_cmd = ['git', 'push', auth_url, current_branch]
            if force:
                push_cmd.append('--force')
                
            res = subprocess.run(push_cmd, cwd=cwd, capture_output=True, text=True)
            
            if res.returncode != 0:
                error_msg = res.stderr
                # Erro comum de histórico divergente
                if "fetch first" in error_msg or "rejected" in error_msg:
                    return False, "REJECTED_HISTORY"
                
                # Push Protection
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
        Runs the atomic update flow: Downloads into a NEW version folder.
        """
        try:
            # 1. Verificar Versão Remota para saber o nome da pasta
            remote_info = Updater.check_remote_version(repo_url, token)
            if not remote_info or 'version' not in remote_info:
                return False, "Não foi possível determinar a versão remota para criar a pasta."
            
            new_v = remote_info['version']
            
            # Subir dois níveis do core/ para a raiz (versions/)
            # Se orquestrado, estamos em versions/vX.Y.Z/core/updater.py
            # A raiz do Orquestrador é '../..' em relação à raiz da versão
            base_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            versions_dir = os.path.join(base_project_dir, "versions")
            target_dir = os.path.join(versions_dir, f"v{new_v}")
            
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir) # Limpa se já existir uma tentativa falha
            
            os.makedirs(target_dir, exist_ok=True)
            
            zip_path = os.path.join(base_project_dir, 'update.zip')
            temp_extract = os.path.join(base_project_dir, 'temp_extract')

            # 2. Download ZIP
            owner_repo = repo_url.replace("https://github.com/", "").replace(".git", "")
            zip_url = f"https://api.github.com/repos/{owner_repo}/zipball/main"
            
            headers = {}
            if token: headers['Authorization'] = f'token {token}'
            
            response = requests.get(zip_url, headers=headers, stream=True)
            if response.status_code != 200:
                return False, f"Falha ao baixar atualização: {response.status_code}"
                
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
            
            # 3. Extrair para a pasta alvo
            if os.path.exists(temp_extract): shutil.rmtree(temp_extract)
            
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(temp_extract)
            
            root_folder = os.listdir(temp_extract)[0]
            inner_dir = os.path.join(temp_extract, root_folder)
            
            # Move conteúdo da extração para target_dir
            for item in os.listdir(inner_dir):
                shutil.move(os.path.join(inner_dir, item), target_dir)
            
            # 4. Criar VENV na nova versão
            logging.info(f"Criando venv para a nova versão v{new_v}...")
            subprocess.run([sys.executable, "-m", "venv", "venv"], cwd=target_dir, check=True)
            
            # 5. Instalar dependências
            req_file = os.path.join(target_dir, 'requirements.txt')
            if os.path.exists(req_file):
                pip_exe = os.path.join(target_dir, "venv", "Scripts", "pip.exe")
                if not os.path.exists(pip_exe): pip_exe = "pip"
                
                logging.info(f"Instalando dependências para v{new_v}...")
                subprocess.run([pip_exe, "install", "-r", "requirements.txt"], cwd=target_dir, check=True)

            # 6. Limpeza
            os.remove(zip_path)
            shutil.rmtree(temp_extract)
            
            return True, f"Atualização v{new_v} preparada com sucesso! O Orquestrador fará a troca em breve."
            
        except Exception as e:
            logging.error(f"Erro crítico na atualização versionada: {e}")
            return False, f"Erro crítico: {str(e)}"
            
        except Exception as e:
            return False, f"Erro crítico na atualização: {str(e)}"
