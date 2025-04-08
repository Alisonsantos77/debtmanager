import pymupdf as pp
import anthropic
import json
import re
from typing import List, Optional
from models.pending_client import PendingClient
from dotenv import load_dotenv
import os
from flet.security import encrypt, decrypt
import logging
from datetime import datetime
import flet as ft
load_dotenv()

# Configurando o logger
logger = logging.getLogger(__name__)


class PDFExtractor:
    def __init__(self, pdf_path: str, page):
        self.pdf_path = pdf_path
        self.page = page
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.MAX_TEXT_LENGTH = 2000  # Limite
        self.SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")

    def validate_pdf_path(self) -> bool:
        """Valida o caminho do PDF com checagens robustas."""
        if not isinstance(self.pdf_path, str):
            logger.error(f"Caminho do PDF inválido: {self.pdf_path} (não é string)")
            self.page.open(ft.SnackBar(ft.Text(f"Erro: Caminho do PDF inválido: {self.pdf_path} (não é string)", color=ft.colors.RED)))
            self.page.update()
            return False

        if not self.pdf_path.lower().endswith('.pdf'):
            logger.error(f"Arquivo não é PDF: {self.pdf_path}")
            self.page.open(ft.SnackBar(ft.Text(f"Erro: O arquivo {self.pdf_path} não é um PDF!", color=ft.colors.RED)))
            self.page.update()
            return False

        if not os.path.exists(self.pdf_path):
            logger.error(f"Arquivo não encontrado: {self.pdf_path}")
            self.page.open(ft.SnackBar(ft.Text(f"Erro: O arquivo {self.pdf_path} não foi encontrado!", color=ft.colors.RED)))
            self.page.update()
            return False

        try:
            with open(self.pdf_path, 'rb') as f:
                if os.path.getsize(self.pdf_path) == 0:
                    logger.warning(f"PDF vazio: {self.pdf_path}")
                    self.page.open(ft.SnackBar(ft.Text(f"Erro: O PDF {self.pdf_path} tá vazio!", color=ft.colors.RED)))
                    self.page.update()
                    return False
            logger.info(f"Caminho do PDF validado: {self.pdf_path}")
            return True
        except PermissionError as e:
            logger.error(f"Permissão negada ao abrir PDF: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Permissão negada ao abrir o PDF. Suporte: {e}", color=ft.colors.RED)))
            self.page.update()
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao validar PDF: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Algo deu errado ao abrir o PDF. Suporte: {e}", color=ft.colors.RED)))
            self.page.update()
            return False

    def extract_text_from_pdf(self) -> str:
        """Extrai texto do PDF com tratamento robusto."""
        if not self.validate_pdf_path():
            return ""

        try:
            doc = pp.open(self.pdf_path)
            if doc.page_count == 0:
                logger.warning(f"PDF sem páginas: {self.pdf_path}")
                self.page.open(ft.SnackBar(
                    ft.Text("Erro: Esse PDF tá vazio ou sem páginas!", color=ft.colors.RED)))
                self.page.update()
                doc.close()
                return ""

            text = ""
            for page in doc:
                page_text = page.get_text("text") or ""
                if not isinstance(page_text, str):
                    logger.warning(f"Texto da página {page.number} não é string: {type(page_text)}")
                    page_text = str(page_text)
                text += page_text + "\n"
            doc.close()

            if not text.strip():
                logger.warning(f"PDF sem texto útil: {self.pdf_path}")
                self.page.open(ft.SnackBar(
                    ft.Text("Erro: Esse PDF não tem texto útil!", color=ft.colors.RED)))
                self.page.update()
                return ""

            logger.info(f"Texto extraído do PDF: {len(text)} caracteres")
            return encrypt(text, self.SECRET_KEY)
        except pp.PyMuPDFError as e:
            logger.error(f"Erro do PyMuPDF ao ler PDF: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Problema ao ler o PDF. Suporte: {e}", color=ft.colors.RED)))
            self.page.update()
            return ""
        except Exception as e:
            logger.error(f"Erro inesperado ao extrair texto: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Algo deu errado ao extrair o texto. Suporte: {e}", color=ft.colors.RED)))
            self.page.update()
            return ""

    def validate_extracted_text(self, text: str) -> bool:
        """Valida se o texto extraído é relevante pra inadimplência."""
        if not isinstance(text, str) or not text.strip():
            logger.warning("Texto extraído inválido ou vazio")
            return False

        try:
            decrypted_text = decrypt(text, self.SECRET_KEY)
            if not decrypted_text.strip():
                logger.warning("Texto descriptografado vazio")
                return False

            # Keywords principais de inadimplência
            keywords = ["inadimplente", "inadimplência", "atraso", "renegociado", "vencimento", "dívida", "pendente"]
            # Keywords adicionais pra reforçar contexto financeiro
            financial_keywords = ["valor", "pagamento", "cliente", "cpf", "cnpj", "telefone"]

            has_main_keywords = any(keyword.lower() in decrypted_text.lower() for keyword in keywords)
            has_financial_context = any(keyword.lower() in decrypted_text.lower() for keyword in financial_keywords)

            if has_main_keywords and has_financial_context:
                logger.info("Texto validado como relatório de inadimplência")
                return True
            else:
                logger.warning("Texto não parece ser um relatório de inadimplência válido")
                self.page.overlay.append(ft.SnackBar(
                    ft.Text("Aviso: Esse PDF não parece ser um relatório de inadimplência!", color=ft.colors.YELLOW)))
                self.page.update()
                return False
        except Exception as e:
            logger.error(f"Erro ao validar texto extraído: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Problema ao validar o texto extraído. Suporte: {e}", color=ft.colors.RED)))
            self.page.update()
            return False

    def extract_clients_with_claude(self, text: str) -> List[dict]:
        """Extrai clientes usando Claude com tratamento de falhas."""
        if not self.validate_extracted_text(text):
            return []

        try:
            decrypted_text = decrypt(text, self.SECRET_KEY)
            prompt = (
                "Você recebeu um relatório financeiro em português. Identifique tabelas ou listas de clientes pendentes. "
                "As colunas podem incluir: Nome/Cliente, CPF/CNPJ, Valor/Dívida, Vencimento/Data, Status/Situação, Contato/Telefone. "
                "Extraia os dados e retorne como um array JSON com os campos: "
                "id (CPF/CNPJ, sem espaços, pontos ou traços), name (Nome/Cliente), debt_amount (Valor/Dívida, sem 'R$', convertido pra float), "
                "due_date (Vencimento/Data, formato DD/MM/YYYY), status (Status/Situação, ex.: 'Em atraso'), "
                "contact (Contato/Telefone, formato (XX) XXXXX-XXXX). "
                "Se uma coluna estiver ausente ou com nome diferente, infira pelo contexto. "
                "Retorne o resultado como array JSON dentro de um bloco Markdown (```json ... ```). "
                "Se não houver dados válidos, retorne um array vazio. "
                f"{decrypted_text[:self.MAX_TEXT_LENGTH]}"
            )
            message = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)

            if not json_match:
                logger.warning("Resposta do Claude não contém JSON válido")
                self.page.open(ft.SnackBar(
                    ft.Text("Erro: Resposta do Claude não contém JSON válido!", color=ft.colors.RED)))
                self.page.update()
                return []

            try:
                clients_data = json.loads(json_match.group(1))
                if not isinstance(clients_data, list):
                    logger.warning(f"JSON não é uma lista: {type(clients_data)}")
                    return []
                logger.info(f"Extraídos {len(clients_data)} clientes do Claude")
                return clients_data
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao parsear JSON do Claude: {e}")
                self.page.open(ft.SnackBar(
                    ft.Text(f"Erro: Problema ao interpretar o JSON do Claude. Suporte: {e}", color=ft.colors.RED)))
                self.page.update()
                return []
        except anthropic.APIError as e:
            logger.error(f"Erro na API do Anthropic: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Problema na API do Claude. Suporte: {e}", color=ft.colors.RED)))
            self.page.update()
            return []
        except Exception as e:
            logger.error(f"Erro inesperado ao extrair com Claude: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Algo deu errado ao extrair com Claude. Suporte: {e}", color=ft.colors.RED)))
            self.page.update()
            return []

    def validate_client_data(self, client_data: dict) -> Optional[dict]:
        """Valida e sanitiza os dados de um cliente."""
        required_fields = {"id", "name", "debt_amount", "due_date", "status", "contact"}
        if not isinstance(client_data, dict) or not all(field in client_data for field in required_fields):
            logger.warning(f"Dados de cliente inválidos: {client_data}")
            return None

        sanitized_data = {}

        # Validação e sanitização do ID (CPF/CNPJ)
        id_str = str(client_data["id"]).replace(" ", "").replace(".", "").replace("-", "").replace("/", "")
        if not (11 <= len(id_str) <= 14 and id_str.isdigit()):
            logger.warning(f"ID inválido: {client_data['id']}")
            return None
        sanitized_data["id"] = id_str

        name = str(client_data["name"]).strip()
        if not name or len(name) < 2:
            logger.warning(f"Nome inválido: {name}")
            return None
        sanitized_data["name"] = name

        # Valor da dívida
        try:
            debt_amount = float(str(client_data["debt_amount"]).replace(",", ".").replace("R$", "").strip())
            if debt_amount <= 0:
                logger.warning(f"Valor da dívida inválido: {debt_amount}")
                return None
            sanitized_data["debt_amount"] = debt_amount
        except (ValueError, TypeError):
            logger.warning(f"Erro ao converter valor da dívida: {client_data['debt_amount']}")
            return None

        # Data de vencimento
        due_date = str(client_data["due_date"]).strip()
        try:
            datetime.strptime(due_date, "%d/%m/%Y")
            sanitized_data["due_date"] = due_date
        except ValueError:
            logger.warning(f"Data de vencimento inválida: {due_date}")
            return None

        # Status
        status = str(client_data["status"]).strip().lower()
        valid_statuses = {"em atraso", "renegociado", "pendente", "vencido", "aberto"}
        if not status or status not in valid_statuses:
            logger.warning(f"Status inválido: {status}")
            return None
        sanitized_data["status"] = status.capitalize()

        # Contato (telefone)
        contact = str(client_data["contact"]).strip()
        contact_clean = re.sub(r"[^\d]", "", contact)
        if not (10 <= len(contact_clean) <= 11) or not contact_clean.isdigit():
            logger.warning(f"Contato inválido: {contact}")
            return None
        formatted_contact = f"({contact_clean[:2]}) {contact_clean[2:7]}-{contact_clean[7:]}"
        sanitized_data["contact"] = formatted_contact

        logger.info(f"Dados do cliente validados: {sanitized_data}")
        return sanitized_data

    def extract_pending_data(self) -> List[PendingClient]:
        """Extrai dados de clientes pendentes com validação robusta."""
        extracted_text = self.extract_text_from_pdf()
        if not extracted_text:
            logger.info("Nenhum texto extraído, retornando lista vazia")
            return []

        clients_data = self.extract_clients_with_claude(extracted_text)
        if not clients_data:
            logger.info("Nenhum cliente extraído pelo Claude")
            return []

        clients = []
        for client_data in clients_data:
            validated_data = self.validate_client_data(client_data)
            if validated_data:
                clients.append(PendingClient(
                    name=validated_data["name"],
                    debt_amount=f"R$ {validated_data['debt_amount']:.2f}".replace(".", ","),
                    due_date=validated_data["due_date"],
                    status=validated_data["status"],
                    contact=validated_data["contact"]
                ))
            else:
                logger.warning(f"Cliente descartado por validação: {client_data}")

        logger.info(f"Extração concluída: {len(clients)} clientes válidos")
        return clients
