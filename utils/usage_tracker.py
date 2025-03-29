import logging
from utils.supabase_utils import write_supabase

logger = logging.getLogger(__name__)


class UsageTracker:
    def __init__(self, user_plan, user_id):
        self.user_plan = user_plan
        self.user_id = user_id
        self.usage = {"messages_sent": 0, "pdfs_processed": 0}

    def increment_usage(self, key, amount=1):
        self.usage[key] += amount

    def check_usage_limits(self, key):
        limits = {"message": 100, "pdf": 5}
        return self.usage[f"{key}s_sent" if key == "message" else f"{key}s_processed"] < limits[key]

    def get_usage(self, key):
        return self.usage[key]

    def sync_with_supabase(self, user_id):
        if not user_id or user_id == "default_user_id":
            logger.error(f"ID de usuário inválido: {user_id}")
            return False
        data = {"messages_sent": self.usage["messages_sent"], "pdfs_processed": self.usage["pdfs_processed"]}
        try:
            response = write_supabase(f"users_debt?id=eq.{user_id}", data, method="patch")
            if response:
                logger.info(f"Uso sincronizado para user_id {user_id}: {data}")
                return True
            else:
                logger.error(f"Falha ao sincronizar uso para user_id {user_id}: resposta vazia")
                return False
        except Exception as e:
            logger.error(f"Erro ao sincronizar com Supabase para user_id {user_id}: {e}")
            return False
