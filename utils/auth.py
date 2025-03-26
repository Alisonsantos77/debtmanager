import asyncio
import os
import logging
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import flet as ft
from flet.security import decrypt

load_dotenv()

SUPABASE_KEY_USERS = os.getenv("SUPABASE_KEY_USERS")
SUPABASE_URL_USERS = os.getenv("SUPABASE_URL_USERS")
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
LOCAL_TIMEZONE = pytz.timezone("America/Sao_Paulo")

logger = logging.getLogger(__name__)


def validate_user(username: str, password: str) -> tuple:
    headers = {"apikey": SUPABASE_KEY_USERS, "Authorization": f"Bearer {SUPABASE_KEY_USERS}"}
    url = f"{SUPABASE_URL_USERS}/rest/v1/users_debt?username=eq.{username}&select=*"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        if not user_data:
            logging.warning(f"Usuário {username} não encontrado.")
            return "invalid", None
        user = user_data[0]
        decrypted_password = decrypt(user['password_hash'], SECRET_KEY)
        if decrypted_password != password:
            logging.warning(f"Senha incorreta para o usuário {username}.")
            return "invalid", None
        if user['status'] != "ativo":
            logging.warning(f"Usuário {username} não está ativo (status: {user['status']}).")
            return "inactive", user
        return "success", user
    except requests.RequestException as e:
        logging.error(f"Erro ao verificar o usuário {username}: {e}")
        return "invalid", None


def user_inative(user_id: str):
    headers = {"apikey": SUPABASE_KEY_USERS,
               "Authorization": f"Bearer {SUPABASE_KEY_USERS}", "Content-Type": "application/json"}
    update_url = f"{SUPABASE_URL_USERS}/rest/v1/users_debt?id=eq.{user_id}"
    data = {"status": "inativo"}
    try:
        response = requests.patch(update_url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"Usuário {user_id} inativado com sucesso.")
    except requests.RequestException as e:
        logger.error(f"Erro ao inativar o usuário {user_id}: {e}")


def update_user_last_login(user_id: str, last_login: str):
    headers = {"apikey": SUPABASE_KEY_USERS,
               "Authorization": f"Bearer {SUPABASE_KEY_USERS}", "Content-Type": "application/json"}
    update_url = f"{SUPABASE_URL_USERS}/rest/v1/users_debt?id=eq.{user_id}"
    try:
        last_login_datetime = datetime.fromisoformat(last_login)
        local_last_login = last_login_datetime.astimezone(LOCAL_TIMEZONE)
        data = {"last_login": local_last_login.isoformat()}
        response = requests.patch(update_url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"Último login do usuário {user_id} atualizado.")
    except requests.RequestException as e:
        logger.error(f"Erro ao atualizar o último login do usuário {user_id}: {e}")


def user_is_active(user_id: str):
    headers = {"apikey": SUPABASE_KEY_USERS, "Authorization": f"Bearer {SUPABASE_KEY_USERS}"}
    url = f"{SUPABASE_URL_USERS}/rest/v1/users_debt?id=eq.{user_id}&select=status"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        if not user_data or user_data[0]['status'] != "ativo":
            return False
        return True
    except requests.RequestException as e:
        logger.error(f"Erro ao verificar o usuário {user_id}: {e}")
        return False


def verificar_status_usuario(page):
    try:
        user_id = page.client_storage.get("user_id")
        if page.route in ["/login", "/register"]:
            return
        if not user_id or not user_is_active(user_id):
            page.client_storage.clear()
            page.go("/login")
            logger.info("Usuário inativo ou não encontrado, redirecionando para login.")
    except Exception as e:
        logger.error(f"Erro ao verificar o status do usuário: {e}")
