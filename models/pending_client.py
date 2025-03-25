from dataclasses import dataclass


@dataclass
class PendingClient:
    name: str
    debt_amount: str
    due_date: str
    status: str
    contact: str
    reason: str = "pendência"

    def format_whatsapp_message(self) -> str:
        return (f"Olá {self.name.split()[0]}, sua fatura de {self.debt_amount} "
                f"venceu em {self.due_date} e está {self.status}. "
                f"Favor regularizar. Contato: {self.contact}.")
