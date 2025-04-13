import os
from dotenv import load_dotenv
import logging
import flet as ft
from supabase import create_client, Client
from flet.security import decrypt

load_dotenv()
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL_USERS")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_USERS")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error(
        f"Erro: Variáveis do Supabase não encontradas! SUPABASE_URL={SUPABASE_URL}, SUPABASE_KEY={SUPABASE_KEY}")
    raise ValueError("SUPABASE_URL e SUPABASE_KEY são obrigatórios. Verifique o arquivo .env.")

# Inicializa o cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def read_supabase(table: str, query: str, page: ft.Page):
    """Lê dados de uma tabela do Supabase usando o SDK."""
    try:
        filters = parse_query(query)
        query_builder = supabase.table(table).select("*")

        for key, value in filters.items():
            if key == 'eq':
                for field, val in value.items():
                    query_builder = query_builder.eq(field, val)

        response = query_builder.execute()
        return response.data
    except Exception as e:
        logger.error(f"Erro ao ler Supabase ({table}): {e}")
        page.open(ft.SnackBar(ft.Text(f"Erro ao consultar dados: {e}", color=ft.Colors.ERROR)))
        return None


def write_supabase(table: str, data: dict, method: str = "post", page: ft.Page = None):
    """Escreve ou atualiza dados no Supabase usando o SDK."""
    try:
        table_name = table
        filters = {}
        if '?' in table:
            table_name, query = table.split('?', 1)
            filters = parse_query(query)

        if method.lower() == "post":
            response = supabase.table(table_name).insert(data).execute()
        elif method.lower() == "patch":
            query_builder = supabase.table(table_name).update(data)
            if filters:
                for key, value in filters.items():
                    if key == 'eq':
                        for field, val in value.items():
                            query_builder = query_builder.eq(field, val)
            elif 'id' in data:
                query_builder = query_builder.eq('id', data['id'])
            else:
                logger.error("Patch precisa de 'id' no data ou filtros REST")
                return False
            response = query_builder.execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Erro ao escrever no Supabase ({table}): {e}")
        if page:
            page.open(ft.SnackBar(ft.Text(f"Erro ao salvar dados: {e}", color=ft.Colors.ERROR)))
        return False


def fetch_user_id(username: str, page: ft.Page):
    """Busca o ID do usuário pelo username."""
    try:
        response = supabase.table("users_debt").select("id").eq("username", username).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar user_id para {username}: {e}")
        page.open(ft.SnackBar(ft.Text(f"Erro ao buscar ID do usuário: {e}", color=ft.Colors.ERROR)))
        return None


def fetch_user_data(user_id: str, page: ft.Page):
    """Busca todos os dados do usuário pelo ID."""
    try:
        response = supabase.table("users_debt").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar dados do usuário {user_id}: {e}")
        page.open(ft.SnackBar(ft.Text(f"Erro ao buscar dados do usuário: {e}", color=ft.Colors.ERROR)))
        return None


def fetch_plan_data(plan_id: int, page: ft.Page):
    """Busca dados do plano pelo ID."""
    try:
        response = supabase.table("plans").select("*").eq("id", plan_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar dados do plano {plan_id}: {e}")
        page.open(ft.SnackBar(ft.Text(f"Erro ao buscar dados do plano: {e}", color=ft.Colors.ERROR)))
        return None


def validate_user(username: str, code: str, encrypted: bool = False, page: ft.Page = None):
    """Valida usuário com base no username e código."""
    try:
        response = supabase.table("users_debt").select("*").eq("username", username).execute()
        if response.data:
            user = response.data[0]
            stored_code = user.get("activation_code")
            status = user.get("status")
            if not encrypted:
                if stored_code == code:
                    return status, user
            else:
                try:
                    decrypted_code = decrypt(stored_code, os.getenv("MY_APP_SECRET_KEY"))
                    if decrypted_code == code:
                        return status, user
                except Exception as e:
                    logger.error(f"Erro ao descriptografar código para {username}: {e}")
                    return "invalido", None
        return "invalido", None
    except Exception as e:
        logger.error(f"Erro ao validar usuário {username}: {e}")
        return "invalido", None


def update_user_status(username: str, status: str, additional_data: dict = None, page: ft.Page = None):
    """Atualiza o status do usuário."""
    try:
        user_id = fetch_user_id(username, page)
        if user_id:
            data = {"status": status}
            if additional_data:
                data.update(additional_data)
            response = supabase.table("users_debt").update(data).eq("id", user_id).execute()
            return bool(response.data)
        return False
    except Exception as e:
        logger.error(f"Erro ao atualizar status do usuário {username}: {e}")
        if page:
            page.open(ft.SnackBar(ft.Text(f"Erro ao atualizar status: {e}", color=ft.Colors.ERROR)))
        return False


def update_usage_data(user_id: str, messages_sent: int, pdfs_processed: int, page: ft.Page):
    """Atualiza os dados de uso do usuário."""
    try:
        response = supabase.table("users_debt").update({
            "messages_sent": messages_sent,
            "pdfs_processed": pdfs_processed
        }).eq("id", user_id).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Erro ao atualizar uso do usuário {user_id}: {e}")
        page.open(ft.SnackBar(ft.Text(f"Erro ao atualizar uso: {e}", color=ft.Colors.ERROR)))
        return False


def get_usage_data(user_id: str, page: ft.Page):
    """Busca dados de uso do usuário."""
    try:
        response = supabase.table("users_debt").select(
            "messages_sent, pdfs_processed, plan_id").eq("id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar uso do usuário {user_id}: {e}")
        page.open(ft.SnackBar(ft.Text(f"Erro ao buscar uso: {e}", color=ft.Colors.ERROR)))
        return None


def read_upgrade_request(user_id: str, code: str, page: ft.Page):
    """Busca upgrade_request com múltiplos filtros."""
    try:
        response = supabase.table("upgrade_requests")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("code", code)\
            .eq("status", "pending")\
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Erro ao buscar upgrade request: {e}")
        page.open(ft.SnackBar(ft.Text(f"Erro ao buscar solicitação: {e}", color=ft.Colors.ERROR)))
        return []


def parse_query(query: str) -> dict:
    """Converte query REST (ex.: ?id=eq.123) pra dict pro SDK."""
    if not query:
        return {}
    filters = {}
    query = query.lstrip('?')
    for part in query.split('&'):
        if '=' in part:
            key, value = part.split('=', 1)
            if '.' in value:
                op, val = value.split('.', 1)
                if op not in filters:
                    filters[op] = {}
                filters[op][key] = val
    return filters
