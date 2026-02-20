import os
import sys
import time
import subprocess
import logging
from datetime import datetime

# Configuração de Logs do Orquestrador
logging.basicConfig(
    level=logging.INFO,
    format='[MANAGER] %(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("manager.log"),
        logging.StreamHandler()
    ]
)

class EduAgendaManager:
    def __init__(self):
        self.base_dir = os.getcwd()
        self.versions_dir = os.path.join(self.base_dir, "versions")
        self.shared_dir = os.path.join(self.base_dir, "shared")
        self.data_dir = os.path.join(self.shared_dir, "data")
        self.app_process = None
        
        # Garante diretórios base
        os.makedirs(self.versions_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.shared_dir, "logs"), exist_ok=True)

    def get_latest_version_path(self):
        """Localiza a pasta de versão mais recente (ex: v1.2.0 > v1.1.0)"""
        if not os.path.exists(self.versions_dir):
            return None
            
        versions = [d for d in os.listdir(self.versions_dir) if os.path.isdir(os.path.join(self.versions_dir, d)) and d.startswith('v')]
        if not versions:
            return None
            
        # Ordenação simples por string funciona para v1.2.0, v1.10.0 etc se seguirem o padrão
        import re
        def sort_key(s):
            return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', s)]
            
        versions.sort(key=sort_key, reverse=True)
        return os.path.join(self.versions_dir, versions[0])

    def start_app(self, version_path):
        """Inicia o servidor na versão especificada"""
        env = os.environ.copy()
        env["EDU_DATA_PATH"] = self.data_dir
        env["EDU_DOTENV_PATH"] = os.path.join(self.shared_dir, ".env")
        env["FLASK_ENV"] = "production"
        
        # Localiza o venv da versão
        python_exe = os.path.join(version_path, "venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            python_exe = sys.executable # Fallback para o python do manager se venv falhar
            
        app_py = os.path.join(version_path, "app.py")
        
        logging.info(f"Iniciando EduAgenda: {version_path}")
        
        try:
            self.app_process = subprocess.Popen(
                [python_exe, "app.py"],
                cwd=version_path,
                env=env
            )
            return True
        except Exception as e:
            logging.error(f"Erro ao iniciar App: {e}")
            return False

    def run(self):
        logging.info("Orquestrador EduAgenda Iniciado.")
        
        while True:
            latest_version = self.get_latest_version_path()
            
            if not latest_version:
                logging.warning("Nenhuma versão encontrada em /versions. Aguardando...")
                time.sleep(10)
                continue
                
            if self.app_process is None or self.app_process.poll() is not None:
                # App não está rodando ou crashou
                logging.info("Detectada paralisação do App. Reiniciando...")
                self.start_app(latest_version)
            
            # TODO: Lógica de Hot-Swap (Verificar se surgiu uma versão mais nova que a atual)
            # Por enquanto apenas mantém a mais nova rodando
            
            time.sleep(5)

if __name__ == "__main__":
    manager = EduAgendaManager()
    manager.run()
