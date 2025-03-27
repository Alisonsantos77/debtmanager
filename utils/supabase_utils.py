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
logger = logging.getLogger(__name__)


def read_supabase(endpoint: str, query: str = "") -> dict:
    url = f"{SUPABASE_URL_USERS}/rest/v1/{endpoint}{query}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data[0] if len(data) == 1 else data
    except requests.RequestException as e:
        logger.error(f"Erro na leitura do Supabase: {e}")
        return {}


def write_supabase(endpoint: str, data: dict, method="post") -> bool:
    url = f"{SUPABASE_URL_USERS}/rest/v1/{endpoint}"
    try:
        if method == "post":
            response = requests.post(url, headers=headers, json=data)
        elif method == "patch":
            response = requests.patch(url, headers=headers, json=data)
        else:
            raise ValueError("Método inválido")
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Erro na escrita do Supabase: {e}")
        return False


def fetch_user_id(username: str) -> str:
    data = read_supabase("users_debt", f"?username=eq.{username}")
    return data.get("id", "default_user_id") if data else "default_user_id"


def update_usage_data(user_id: str, messages_sent: int, pdfs_processed: int) -> bool:
    data = {"messages_sent": messages_sent, "pdfs_processed": pdfs_processed}
    return write_supabase(f"users_debt?id=eq.{user_id}", data, method="patch")


def validate_user(username: str, code: str) -> tuple:
    data = read_supabase("users_debt", f"?username=eq.{username}")
    if not data:
        return "invalid", None
    user = data
    if decrypt(user["activation_code"], SECRET_KEY) != code:
        return "invalid", None
    return user["status"], user


def update_user_status(username: str, status: str, extra_data: dict = None):
    data = {"status": status}
    if extra_data:
        data.update(extra_data)
    return write_supabase(f"users_debt?username=eq.{username}", data, method="patch")
