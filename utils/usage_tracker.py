class UsageTracker:
    def __init__(self, user_plan, user_id):
        from utils.supabase_utils import read_supabase
        self.user_plan = user_plan
        user_data = read_supabase("users_debt", f"?id=eq.{user_id}")
        self.usage = {
            "messages_sent": user_data.get("messages_sent", 0),
            "pdfs_processed": user_data.get("pdfs_processed", 0)
        }
        plan_data = read_supabase("plans", f"?name=eq.{user_plan}")
        self.limits = {user_plan: {"messages": plan_data["message_limit"], "pdfs": plan_data["pdf_limit"]}}

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