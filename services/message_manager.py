from typing import List
from models.pending_client import PendingClient
from twilio.rest import Client
import os
from dotenv import load_dotenv
from utils.database import add_notification, save_notification
load_dotenv()


class MessageManager:
    def __init__(self):
        self.TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid")
        self.TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token")
        self.TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.client = Client(self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN)

    def generate_notifications(self, clients: List[PendingClient]) -> None:
        print("\n=== Mensagens simuladas para WhatsApp ===")
        for client in clients:
            print(client.format_whatsapp_message())
        print("====================================\n")

    def send_all_notifications(self, clients: List[PendingClient], custom_message=None) -> None:
        for client in clients:
            self.send_single_notification(client, custom_message)

    def send_single_notification(self, client: PendingClient, custom_message=None) -> bool:
        raw_number = ''.join(filter(str.isdigit, client.contact))
        if len(raw_number) in [10, 11]:
            client_number = f"whatsapp:+55{raw_number}" if len(raw_number) == 11 else f"whatsapp:+5511{raw_number}"
            message_body = (custom_message.format(name=client.name.split()[0], debt_amount=client.debt_amount,
                                                  due_date=client.due_date) if custom_message else client.format_whatsapp_message())
            try:
                message = self.client.messages.create(
                    body=message_body,
                    from_=self.TWILIO_WHATSAPP_NUMBER,
                    to=client_number
                )
                if message.sid:
                    print(f"Mensagem enviada para {client.name}: SID {message.sid}")
                    add_notification(client.name, message_body, "Success", message.sid)
                    return True
                return False
            except Exception as e:
                print(f"Erro ao enviar mensagem para {client.name}: {e}")
                add_notification(client.name, message_body, f"Failed: {str(e)}")
                return False
        else:
            print(f"Número inválido para {client.name}: {client.contact}")
            add_notification(client.name, message_body if custom_message else client.format_whatsapp_message(),
                             "Failed: Invalid number")
            return False
