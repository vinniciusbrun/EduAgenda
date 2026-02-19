import json
import os
import portalocker

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
                portalocker.lock(f, portalocker.LOCK_SH) # Trava de compartilhada (leitura)
                data = json.load(f)
                portalocker.unlock(f)
                return data
        except Exception as e:
            print(f"Erro ao carregar {filename}: {e}")
            return []

    @staticmethod
    def _safe_replace(src, dst):
        import time
        max_retries = 20  # Increased from 5 to 20
        for i in range(max_retries):
            try:
                if os.path.exists(dst):
                    os.replace(src, dst)
                else:
                    os.rename(src, dst)
                return True
            except PermissionError:
                if i == max_retries - 1:
                    print(f"PERM ERROR: Failed to replace {dst} - file locked.")
                    raise
                time.sleep(0.1)  # Fixed sleep 100ms
            except OSError as e:
                print(f"OS ERROR replace: {e}")
                if i == max_retries - 1: raise
                time.sleep(0.1)
                
        print(f"CRITICAL ERROR: Failed to replace {src} with {dst} after retries.")
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
        portalocker.lock(f, portalocker.LOCK_EX)
        try:
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
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            if not DataManager._safe_replace(temp_path, path):
                print(f"ERROR: Could not save {filename} (safe_replace failed)")
                raise Exception(f"Falha ao salvar {filename}")
        finally:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass

def get_professores():
    return DataManager.load('professores.json')

def save_professores(data):
    DataManager.save('professores.json', data)

def get_turmas():
    return DataManager.load('turmas.json')

def save_turmas(data):
    DataManager.save('turmas.json', data)

def get_agendamentos():
    return DataManager.load('agendamentos.json')

def save_agendamentos(data):
    DataManager.save('agendamentos.json', data)

def update_professores(callback):
    return DataManager.update('professores.json', callback)

def update_turmas(callback):
    return DataManager.update('turmas.json', callback)

def update_agendamentos(callback):
    return DataManager.update('agendamentos.json', callback)

def get_recursos():
    return DataManager.load('recursos.json')

def save_recursos(data):
    DataManager.save('recursos.json', data)

def get_usuarios():
    return DataManager.load('usuarios.json')

def save_usuarios(data):
    DataManager.save('usuarios.json', data)

def update_usuarios(callback):
    return DataManager.update('usuarios.json', callback)

def get_config():
    data = DataManager.load('config.json')
    if not data or isinstance(data, list):
        return {"nome_escola": "EduAgenda", "logo_url": None}
    return data

def update_config(callback):
    return DataManager.update('config.json', callback)

def save_config(data):
    DataManager.save('config.json', data)

def get_logs():
    return DataManager.load('logs.json')

def update_logs(callback):
    return DataManager.update('logs.json', callback)
