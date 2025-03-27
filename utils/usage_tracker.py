class UsageTracker:
    def __init__(self, user_plan):
        self.user_plan = user_plan
        self.usage = {"messages_sent": 0, "pdfs_processed": 0}
        self.limits = {
            "basic": {"pdfs": 3, "messages": 5},  # Limites reduzidos para teste
            "pro": {"pdfs": 10, "messages": 20},
            "enterprise": {"pdfs": 50, "messages": 100}
        }

    def check_usage_limits(self, action, count=1):
        if action == "message":
            return self.usage["messages_sent"] + count <= self.limits[self.user_plan]["messages"]
        elif action == "pdf":
            return self.usage["pdfs_processed"] + count <= self.limits[self.user_plan]["pdfs"]
        return False

    def increment_usage(self, action, count=1):
        if action == "messages_sent":
            self.usage["messages_sent"] += count
        elif action == "pdfs_processed":
            self.usage["pdfs_processed"] += count

    def get_usage(self, action):
        return self.usage[action]

    def sync_with_supabase(self, user_id):
        from utils.supabase_utils import update_usage_data
        success = update_usage_data(user_id, self.usage["messages_sent"], self.usage["pdfs_processed"])
        return success
