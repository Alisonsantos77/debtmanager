import requests
import os
import logging
from dotenv import load_dotenv
from flet.security import decrypt, encrypt
import flet as ft

load_dotenv()

SUPABASE_KEY_USERS = os.getenv("SUPABASE_KEY_USERS")
SUPABASE_URL_USERS = os.getenv("SUPABASE_URL_USERS")
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")
headers = {"apikey": SUPABASE_KEY_USERS, "Authorization": f"Bearer {SUPABASE_KEY_USERS}", "Content-Type": "application/json"}

logger = logging.getLogger(__name__)


def read_supabase(endpoint: str, query: str = "", page: ft.Page = None) -> dict:
    url = f"{SUPABASE_URL_USERS}/rest/v1/{endpoint}{query}"
    logger.info(f"Tentando ler do Supabase: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Dados lidos com sucesso: {len(data)} registros")
        return data[0] if len(data) == 1 else data
    except requests.RequestException as e:
        logger.error(f"Erro ao ler do Supabase: {e}")
        if page:
            page.overlay.append(ft.SnackBar(
                ft.Text("Ops, algo deu errado ao carregar os dados. Tente de novo!"), bgcolor=ft.colors.RED))
            page.update()
        return {}


def write_supabase(endpoint: str, data: dict, method="post", page: ft.Page = None) -> bool:
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
        logger.info(f"Escrita bem-sucedida: {response.status_code}")
        return True
    except requests.RequestException as e:
        logger.error(f"Erro ao escrever no Supabase: {e}")
        if page:
            page.overlay.append(ft.SnackBar(
                ft.Text("Deu ruim ao salvar os dados. Tenta novamente?"), bgcolor=ft.colors.RED))
            page.update()
        return False


def fetch_user_id(username: str, page: ft.Page = None) -> str:
    logger.info(f"Buscando user_id para username: {username}")
    data = read_supabase("users_debt", f"?username=eq.{username}", page)
    user_id = data.get("id") if data else None
    if not user_id:
        logger.error(f"User_id não encontrado para username: {username}")
        if page:
            page.overlay.append(ft.SnackBar(ft.Text("Usuário não encontrado. Verifica o nome!"), bgcolor=ft.colors.RED))
            page.update()
    return user_id


def fetch_user_data(user_id: str, page: ft.Page = None) -> dict:
    logger.info(f"Buscando dados do usuário para user_id: {user_id}")
    data = read_supabase("users_debt", f"?id=eq.{user_id}", page)
    if not data:
        logger.error(f"Dados do usuário não encontrados para user_id: {user_id}")
        if page:
            page.overlay.append(ft.SnackBar(
                ft.Text("Não consegui pegar seus dados. Tenta relogar?"), bgcolor=ft.colors.RED))
            page.update()
    return data


def fetch_plan_data(plan_id: int, page: ft.Page = None) -> dict:
    logger.info(f"Buscando dados do plano para plan_id: {plan_id}")
    data = read_supabase("plans", f"?id=eq.{plan_id}", page)
    if not data:
        logger.error(f"Plano não encontrado para plan_id: {plan_id}")
        if page:
            page.overlay.append(ft.SnackBar(ft.Text("Plano não encontrado. Algo tá estranho!"), bgcolor=ft.colors.RED))
            page.update()
    return data


def update_usage_data(user_id: str, messages_sent: int, pdfs_processed: int, page: ft.Page = None) -> bool:
    data = {"messages_sent": messages_sent, "pdfs_processed": pdfs_processed}
    logger.info(f"Atualizando uso para user_id {user_id}: {data}")
    success = write_supabase(f"users_debt?id=eq.{user_id}", data, method="patch", page=page)
    if success:
        logger.info("Atualização de uso concluída com sucesso")
    else:
        logger.error("Falha ao atualizar uso")
    return success


def validate_user(username: str, code: str, encrypted: bool = False, page: ft.Page = None) -> tuple:
    logger.info(f"Validando usuário: {username}")
    data = read_supabase("users_debt", f"?username=eq.{username}", page)
    if not data:
        logger.warning(f"Usuário {username} não encontrado")
        if page:
            page.overlay.append(ft.SnackBar(
                ft.Text("Esse usuário não existe. Tá certo o nome?"), bgcolor=ft.colors.RED))
            page.update()
        return "not_found", None
    user = data
    try:
        stored_code = user["activation_code"]
        if encrypted and code:
            decrypted_code = decrypt(stored_code, SECRET_KEY)
            if decrypted_code != code:
                logger.warning(f"Código inválido para {username}")
                if page:
                    page.overlay.append(ft.SnackBar(ft.Text("Código errado. Tenta outro!"), bgcolor=ft.colors.RED))
                    page.update()
                return "invalid_code", None
        logger.info(f"Usuário {username} validado com status: {user['status']}")
        return user["status"], user
    except Exception as e:
        logger.error(f"Erro ao validar código para {username}: {e}")
        if page:
            page.overlay.append(ft.SnackBar(
                ft.Text("Algo deu errado ao validar. Tenta de novo!"), bgcolor=ft.colors.RED))
            page.update()
        return "error", None


def update_user_status(username: str, status: str, extra_data: dict = None, page: ft.Page = None) -> bool:
    data = {"status": status}
    if extra_data:
        data.update(extra_data)
    logger.info(f"Atualizando status de {username} para {status} com dados extras: {extra_data}")
    success = write_supabase(f"users_debt?username=eq.{username}", data, method="patch", page=page)
    if success:
        logger.info("Status atualizado com sucesso")
        if page:
            page.overlay.append(ft.SnackBar(ft.Text(f"Status atualizado pra {status}!"), bgcolor=ft.colors.GREEN))
            page.update()
    else:
        logger.error("Falha ao atualizar status")
    return success
