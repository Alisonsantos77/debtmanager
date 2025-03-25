class UsageTracker:
    def __init__(self, user_plan):
        self.user_plan = user_plan
        self.usage = {"messages_sent": 0, "pdfs_processed": 0}
        self.limits = {
            "basic": {"pdfs": 10, "messages": 50},
            "pro": {"pdfs": 50, "messages": 200},
            "enterprise": {"pdfs": 200, "messages": 1000}
        }

    def check_usage_limits(self, action, count=1):
        if action == "message":
            return self.usage["messages_sent"] + count <= self.limits[self.user_plan]["messages"]
        elif action == "pdf":
            return self.usage["pdfs_processed"] + count <= self.limits[self.user_plan]["pdfs"]
        return False

    def increment_usage(self, action):
        if action == "messages_sent":
            self.usage["messages_sent"] += 1
        elif action == "pdfs_processed":
            self.usage["pdfs_processed"] += 1

    def get_usage(self, action):
        return self.usage[action]
