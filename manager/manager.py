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
            
        versions = [d for d in os.listdir(self.versions_dir) if os.path.isdir(os.path.join(self.versions_dir, d)) and d.startswith('v') and not d.endswith('_FAILED')]
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
            self.last_start_time = time.time()
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
                
            if not hasattr(self, 'current_version_path'):
                self.current_version_path = latest_version
                self.stable_version_path = latest_version
                
            if self.app_process is None or self.app_process.poll() is not None:
                uptime = time.time() - getattr(self, 'last_start_time', 0)
                
                # --- Lógica de Fallback ---
                if self.app_process is not None:
                    if uptime < 15 and self.current_version_path != self.stable_version_path:
                        logging.error(f"CRASH FATAL DETECTADO: Versão {self.current_version_path} quebrou no boot (uptime: {uptime:.1f}s). Acionando FALLBACK...")
                        try:
                            failed_dir = self.current_version_path + "_FAILED"
                            os.rename(self.current_version_path, failed_dir)
                            logging.info(f"Isolando versão instável em: {failed_dir}")
                        except Exception as e:
                            logging.error(f"Erro ao isolar versão: {e}")
                            
                        self.current_version_path = self.stable_version_path
                        logging.info(f"Efetuando downgrade de emergência para a estável: {self.current_version_path}")
                    elif uptime >= 15:
                        # Se sobreviveu mais de 15s, podemos considerar estável para futuros fallbacks
                        self.stable_version_path = self.current_version_path

                # App não está rodando ou crashou
                logging.info(f"Iniciando App (ou reiniciando após queda): {self.current_version_path}")
                self.start_app(self.current_version_path)
            else:
                # App está rodando, podemos atualizar o stable se sobreviveu
                uptime = time.time() - getattr(self, 'last_start_time', 0)
                if uptime >= 15:
                    self.stable_version_path = self.current_version_path
            
            # Hot-Swap Seguro: Verifica se surgiu uma versão mais nova
            if latest_version and latest_version != self.current_version_path and not latest_version.endswith('_FAILED'):
                logging.info(f"Nova versão detectada: {latest_version}. Verificando ociosidade do servidor atual...")
                try:
                    import urllib.request
                    import json
                    req = urllib.request.urlopen("http://127.0.0.1:5000/api/sys/status", timeout=2)
                    status_data = json.loads(req.read().decode())
                    idle = status_data.get("idle_seconds", 0)
                    
                    if idle > 180:  # 3 minutos ocioso para atualizar silenciosamente
                        logging.info(f"Servidor ocioso por {int(idle)}s. Aplicando atualização Hot-Swap para {latest_version}...")
                        self.stable_version_path = self.current_version_path # Guarda a atual como estável antes de trocar
                        
                        if self.app_process:
                            self.app_process.terminate()
                            try:
                                self.app_process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                self.app_process.kill()
                        
                        self.current_version_path = latest_version
                        self.start_app(latest_version)
                    else:
                        logging.info(f"Servidor ativo (idle={int(idle)}s). Aguardando 3 minutos de inatividade para atualizar...")
                except Exception as e:
                    logging.warning(f"Não foi possível checar o status (Offline ou Inicializando). Tentando forçar update logo. Erro: {e}")
                    self.stable_version_path = self.current_version_path
                    if self.app_process:
                        self.app_process.kill()
                    self.current_version_path = latest_version
                    self.start_app(latest_version)
            
            time.sleep(5)

if __name__ == "__main__":
    manager = EduAgendaManager()
    manager.run()
