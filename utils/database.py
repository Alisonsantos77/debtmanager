from datetime import datetime
from typing import List, NamedTuple
import os
from flet.security import encrypt, decrypt


class Notification(NamedTuple):
    sent_at: str
    status: str
    message: str
    sid: str = None


notification_history = {}


def save_notification(client_name: str, message: str, status: str):
    secret_key = os.getenv("MY_APP_SECRET_KEY")
    encrypted_contact = encrypt(client_name, secret_key)
    if client_name not in notification_history:
        notification_history[client_name] = []
    notification_history[client_name].append(Notification(
        sent_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        status=status,
        message=message
    ))


def add_notification(client_name: str, message: str, status: str, sid: str = None):
    secret_key = os.getenv("MY_APP_SECRET_KEY")
    encrypted_contact = encrypt(client_name, secret_key)
    if client_name not in notification_history:
        notification_history[client_name] = []
    notification_history[client_name].append(Notification(
        sent_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        status=status,
        message=message,
        sid=sid
    ))


def get_client_history(client_name: str) -> List[Notification]:
    return notification_history.get(client_name, [])


def log_action(user_id: str, action: str):
    log_dir = os.path.join(os.getenv("FLET_APP_STORAGE_TEMP"), "audit_logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "audit_log.txt")
    with open(log_path, "a") as f:
        f.write(f"{datetime.now()}: User {user_id} - {action}\n")
