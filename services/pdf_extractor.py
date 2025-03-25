import pymupdf as pp
import anthropic
import json
import re
from typing import List
from models.pending_client import PendingClient
from dotenv import load_dotenv
import os

load_dotenv()


class PDFExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.MAX_TEXT_LENGTH = 10000

    def validate_pdf_path(self) -> bool:
        if not isinstance(self.pdf_path, str) or not self.pdf_path.lower().endswith('.pdf'):
            print(f"Erro: Arquivo deve ser um PDF válido, recebido: {self.pdf_path}")
            return False
        try:
            with open(self.pdf_path, 'rb'):
                return True
        except Exception as e:
            print(f"Erro ao acessar o PDF: {e}")
            return False

    def extract_text_from_pdf(self) -> str:
        if not self.validate_pdf_path():
            return ""
        try:
            doc = pp.open(self.pdf_path)
            text = "\n".join(page.get_text("text") or "" for page in doc)
            doc.close()
            return text if text.strip() else ""
        except Exception as e:
            print(f"Erro ao extrair texto do PDF: {e}")
            return ""

    def validate_extracted_text(self, text: str) -> bool:
        keywords = ["inadimplente", "inadimplência", "atraso", "renegociado", "vencimento", "dívida"]
        return isinstance(text, str) and any(keyword.lower() in text.lower() for keyword in keywords)

    def extract_clients_with_claude(self, text: str) -> List[dict]:
        if not self.validate_extracted_text(text):
            return []
        prompt = (
            "You are given a financial report in Portuguese. Identify any table or list containing pending clients. "
            "The table or list may have columns such as: Nome/Cliente, CPF/CNPJ, Valor/Dívida, Vencimento/Data, Status/Situação, Contato/Telefone. "
            "Extract the data and return it as a JSON array of objects with these fields: "
            "id (CPF/CNPJ, remove spaces, dots, and dashes), name (Nome/Cliente), debt_amount (Valor/Dívida, remove 'R$' and convert to float), "
            "due_date (Vencimento/Data, in DD/MM/YYYY format), status (Status/Situação, e.g., 'Em atraso' or 'Renegociado'), "
            "contact (Contato/Telefone, in (XX) XXXXX-XXXX format). "
            "If a column is missing or named differently, infer the data based on context. "
            "Return the result as a JSON array, wrapped in a Markdown code block (```json ... ```). "
            f"{text[:self.MAX_TEXT_LENGTH]}"
        )
        try:
            message = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            return json.loads(json_match.group(1)) if json_match else []
        except Exception as e:
            print(f"Erro ao processar resposta da API: {e}")
            return []

    def validate_client_data(self, client_data: dict) -> bool:
        required_fields = ["id", "name", "debt_amount", "due_date", "status", "contact"]
        for field in required_fields:
            if field not in client_data:
                return False
        try:
            float(client_data["debt_amount"])
            from datetime import datetime
            datetime.strptime(client_data["due_date"], "%d/%m/%Y")
        except (ValueError, TypeError):
            return False
        return True

    def extract_pending_data(self) -> List[PendingClient]:
        extracted_text = self.extract_text_from_pdf()
        if not extracted_text:
            return []
        clients_data = self.extract_clients_with_claude(extracted_text)
        clients = []
        for client_data in clients_data:
            if self.validate_client_data(client_data):
                clients.append(PendingClient(
                    name=client_data["name"].strip(),
                    debt_amount=f"R$ {float(client_data['debt_amount']):.2f}".replace(".", ","),
                    due_date=client_data["due_date"],
                    status=client_data["status"],
                    contact=client_data["contact"]
                ))
        return clients
