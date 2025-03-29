import requests
import os
import logging
from dotenv import load_dotenv
from flet.security import decrypt, encrypt

load_dotenv()

SUPABASE_KEY_USERS = os.getenv("SUPABASE_KEY_USERS")
SUPABASE_URL_USERS = os.getenv("SUPABASE_URL_USERS")
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")
headers = {"apikey": SUPABASE_KEY_USERS, "Authorization": f"Bearer {SUPABASE_KEY_USERS}", "Content-Type": "application/json"}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)


def read_supabase(endpoint: str, query: str = "") -> dict:
    url = f"{SUPABASE_URL_USERS}/rest/v1/{endpoint}{query}"
    logger.info(f"Lendo Supabase: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Dados retornados do Supabase: {data}")
        return data[0] if len(data) == 1 else data
    except requests.RequestException as e:
        logger.error(f"Erro na leitura do Supabase: {e}")
        return {}


def write_supabase(endpoint: str, data: dict, method="post") -> bool:
    url = f"{SUPABASE_URL_USERS}/rest/v1/{endpoint}"
    logger.info(f"Escrevendo no Supabase: {url} com método {method} e dados {data}")
    try:
        if method == "post":
            response = requests.post(url, headers=headers, json=data)
        elif method == "patch":
            response = requests.patch(url, headers=headers, json=data)
        else:
            raise ValueError("Método inválido")
        response.raise_for_status()
        logger.info(f"Escrita no Supabase bem-sucedida: {response.status_code}")
        return True
    except requests.RequestException as e:
        logger.error(f"Erro na escrita do Supabase: {e}")
        return False


def fetch_user_id(username: str) -> str:
    logger.info(f"Buscando user_id para username: {username}")
    data = read_supabase("users_debt", f"?username=eq.{username}")
    user_id = data.get("id") if data else None
    if not user_id:
        logger.error(f"User_id não encontrado para username: {username}")
        return None
    logger.info(f"User_id retornado: {user_id}")
    return user_id


def update_usage_data(user_id: str, messages_sent: int, pdfs_processed: int) -> bool:
    data = {"messages_sent": messages_sent, "pdfs_processed": pdfs_processed}
    logger.info(f"Atualizando uso para user_id {user_id}: {data}")
    success = write_supabase(f"users_debt?id=eq.{user_id}", data, method="patch")
    logger.info(f"Atualização de uso {'bem-sucedida' if success else 'falhou'}")
    return success


def validate_user(username: str, code: str) -> tuple:
    logger.info(f"Validando usuário: {username}")
    data = read_supabase("users_debt", f"?username=eq.{username}")
    if not data:
        logger.warning(f"Usuário {username} não encontrado")
        return "invalid", None
    user = data
    try:
        decrypted_code = decrypt(user["activation_code"], SECRET_KEY)
        logger.info(f"Código descriptografado para {username}")
        if decrypted_code != code:
            logger.warning(f"Código inválido para {username}")
            return "invalid", None
        logger.info(f"Usuário {username} validado com status: {user['status']}")
        return user["status"], user
    except Exception as e:
        logger.error(f"Erro ao descriptografar código para {username}: {e}")
        return "invalid", None


def update_user_status(username: str, status: str, extra_data: dict = None):
    data = {"status": status}
    if extra_data:
        data.update(extra_data)
    logger.info(f"Atualizando status do usuário {username} para {status} com dados extras: {extra_data}")
    success = write_supabase(f"users_debt?username=eq.{username}", data, method="patch")
    logger.info(f"Atualização de status {'bem-sucedida' if success else 'falhou'}")
    return success
