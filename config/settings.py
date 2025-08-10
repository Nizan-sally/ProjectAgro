import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

def get_secret_key():
    """Gera ou recupera uma chave secreta segura."""
    if not os.getenv("SECRET_KEY"):
        import secrets
        return secrets.token_hex(32)
    return os.getenv("SECRET_KEY")

# Configurações de alerta
ALERT_RECIPIENTS = {
    "telegram": [int(id) for id in os.getenv("TELEGRAM_IDS", "").split(",")] if os.getenv("TELEGRAM_IDS") else [],
    "email": os.getenv("ALERT_EMAILS", "").split(",") if os.getenv("ALERT_EMAILS") else []
}

# Configurações do banco
DB_PATH = os.getenv("DB_PATH", "agroinsight.db")

# Configurações de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/agroinsight.log")