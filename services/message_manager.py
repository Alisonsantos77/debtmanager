import datetime
import logging
import os
from typing import List

import flet as ft
from dotenv import load_dotenv
from flet.security import decrypt, encrypt
from twilio.rest import Client

from models.pending_client import PendingClient
from utils.database import add_notification, save_notification

load_dotenv()

logger = logging.getLogger(__name__)


class MessageManager:
    def __init__(self, page=None):
        secret_key = os.getenv("MY_APP_SECRET_KEY")
        encrypted_sid = encrypt(os.getenv("TWILIO_ACCOUNT_SID"), secret_key)
        encrypted_token = encrypt(os.getenv("TWILIO_AUTH_TOKEN"), secret_key)
        self.TWILIO_ACCOUNT_SID = decrypt(encrypted_sid, secret_key)
        self.TWILIO_AUTH_TOKEN = decrypt(encrypted_token, secret_key)
        self.TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.client = Client(self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN)
        self.daily_limits = {}  # Controle de mensagens por número por dia
        self.notified_numbers = set()  # Conjunto para controlar números já notificados sobre limite
        self.MAX_DAILY_MESSAGES = 1  # Limite diário por número
        self.page = page

    def show_limit_warning(self, client_number, client_name):
        if client_number not in self.notified_numbers:
            self.notified_numbers.add(client_number)
            snackbar = ft.SnackBar(
                content=ft.Text(
                    f"Limite diário excedido para {client_name} ({client_number}). Próxima tentativa após meia-noite.",
                    color=ft.Colors.ON_ERROR_CONTAINER
                ),
                bgcolor=ft.Colors.ERROR_CONTAINER,
                duration=4000,
                show_close_icon=True
            )
            if self.page:
                self.page.overlay.append(snackbar)
                snackbar.open = True
                self.page.update()

    def reset_daily_limits(self):
        """Reseta os limites diários e o conjunto de números notificados"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        for number, data in self.daily_limits.items():
            if data["date"] != today:
                self.daily_limits[number] = {"date": today, "count": 0}
        self.notified_numbers.clear()  # Limpa o conjunto de números notificados

    def check_daily_limit(self, phone_number):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if phone_number not in self.daily_limits:
            self.daily_limits[phone_number] = {"date": today, "count": 0}

        if self.daily_limits[phone_number]["date"] != today:
            self.daily_limits[phone_number] = {"date": today, "count": 0}
            if phone_number in self.notified_numbers:
                self.notified_numbers.remove(phone_number)

        return self.daily_limits[phone_number]["count"] < self.MAX_DAILY_MESSAGES

    def increment_daily_count(self, phone_number):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if phone_number not in self.daily_limits:
            self.daily_limits[phone_number] = {"date": today, "count": 0}

        if self.daily_limits[phone_number]["date"] != today:
            self.daily_limits[phone_number] = {"date": today, "count": 0}

        self.daily_limits[phone_number]["count"] += 1

    def generate_notifications(self, clients: List[PendingClient]) -> None:
        for client in clients:
            print(client.format_whatsapp_message())

    def send_all_notifications(self, clients: List[PendingClient], custom_message=None) -> None:
        for client in clients:
            self.send_single_notification(client, custom_message)

    def send_single_notification(self, client: PendingClient, custom_message=None) -> bool:
        raw_number = ''.join(filter(str.isdigit, client.contact))
        if len(raw_number) in [10, 11]:
            client_number = f"whatsapp:+55{raw_number}" if len(raw_number) == 11 else f"whatsapp:+5511{raw_number}"

            # Verifica limite diário
            if not self.check_daily_limit(client_number):
                logger.warning(f"Limite diário excedido para {client.name} ({client_number})")
                add_notification(client.name, custom_message if custom_message else client.format_whatsapp_message(),
                                 "Falha: Limite diário de mensagens excedido")
                self.show_limit_warning(client_number, client.name)
                return False

            message_body = (custom_message.format(name=client.name.split()[0], debt_amount=client.debt_amount,
                                                  due_date=client.due_date) if custom_message else client.format_whatsapp_message())
            try:
                message = self.client.messages.create(
                    body=message_body,
                    from_=self.TWILIO_WHATSAPP_NUMBER,
                    to=client_number
                )
                if message.sid:
                    logger.info(f"Mensagem enviada para {client.name}: SID {message.sid}")
                    add_notification(client.name, message_body, "Success", message.sid)
                    self.increment_daily_count(client_number)
                    return True
                logger.error(f"Falha ao enviar para {client.name}: SID não retornado")
                add_notification(client.name, message_body, "Falha: SID não retornado")
                return False
            except Exception as e:
                error_message = str(e)
                if "invalid phone number" in error_message.lower():
                    logger.error(f"Número inválido para {client.name}: {client.contact}")
                    add_notification(client.name, message_body, "Falha: Número inválido")
                elif "rate limit" in error_message.lower():
                    logger.error(f"Limite de taxa excedido para {client.name}")
                    add_notification(client.name, message_body, "Falha: Limite de taxa excedido")
                elif "blocked" in error_message.lower():
                    logger.error(f"Número bloqueado para {client.name}")
                    add_notification(client.name, message_body, "Falha: Número bloqueado")
                else:
                    logger.error(f"Erro ao enviar mensagem para {client.name}: {error_message}")
                    add_notification(client.name, message_body, f"Falha: {error_message}")
                return False
        else:
            logger.error(f"Número inválido para {client.name}: {client.contact}")
            add_notification(client.name, message_body if custom_message else client.format_whatsapp_message(),
                             "Falha: Número inválido")
            return False
