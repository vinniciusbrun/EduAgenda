import os
import base64
import hashlib
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Carregar variáveis de ambiente para obter a chave secreta
# Localização do .env (Shared se orquestrado)
DOTENV_PATH = os.environ.get('EDU_DOTENV_PATH')
if not DOTENV_PATH:
    # Tenta achar um .env na raiz ou dois níveis acima (versions/vX.Y.Z/ -> root/shared/.env)
    version_root = os.path.dirname(os.path.dirname(__file__))
    # versions/v1.2.0/ -> root/shared/.env
    potential_shared = os.path.join(os.path.dirname(os.path.dirname(version_root)), "shared", ".env")
    if os.path.exists(potential_shared):
        DOTENV_PATH = potential_shared
    else:
        DOTENV_PATH = os.path.join(version_root, ".env")

load_dotenv(DOTENV_PATH)

class SecretManager:
    _fernet = None

    @classmethod
    def _get_fernet(cls):
        if cls._fernet is None:
            # Pega a chave do FLASK_SECRET_KEY ou usa um fallback (não recomendado para produção)
            raw_key = os.getenv('FLASK_SECRET_KEY', 'antigravity-default-security-key-2026')
            
            # Deriva uma chave de 32 bytes compatível com Fernet usando SHA-256
            key_32 = hashlib.sha256(raw_key.encode()).digest()
            fernet_key = base64.urlsafe_b64encode(key_32)
            cls._fernet = Fernet(fernet_key)
        return cls._fernet

    @classmethod
    def reload_key(cls):
        """Recarrega a chave de criptografia do arquivo .env atual."""
        load_dotenv(DOTENV_PATH, override=True)
        cls._fernet = None
        print("🔐 Chave de criptografia recarregada com sucesso.")

    @classmethod
    def encrypt(cls, text: str) -> str:
        """Criptografa um texto e retorna uma string base64."""
        if not text:
            return ""
        try:
            f = cls._get_fernet()
            encrypted_bytes = f.encrypt(text.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            print(f"[SECURITY ERROR] Falha ao criptografar: {e}")
            return text

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        """Descriptografa uma string base64. Retorna o original se não estiver criptografado."""
        if not encrypted_text:
            return ""
        
        # Heurística simples: se não começar com os padrões do Fernet ou falhar, retorna o original
        # Isso permite migração suave de tokens em texto simples
        try:
            f = cls._get_fernet()
            decrypted_bytes = f.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception:
            # Se falhar, assumimos que o token ainda está em texto simples (transição)
            return encrypted_text

    @classmethod
    def is_encrypted(cls, text: str) -> bool:
        """Verifica se o texto parece estar criptografado."""
        if not text: return False
        try:
            f = cls._get_fernet()
            f.decrypt(text.encode())
            return True
        except:
            return False
