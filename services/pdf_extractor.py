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
        self.MAX_TEXT_LENGTH = 10000  # Limite de caracteres pro Claude
        self.SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")
        logger.info(f"Iniciando PDFExtractor para {pdf_path}")

    def validate_pdf_path(self) -> bool:
        """Valida o caminho do PDF com checagens robustas."""
        logger.info(f"Validando caminho do PDF: {self.pdf_path}")
        if not isinstance(self.pdf_path, str):
            logger.error(f"Caminho do PDF inválido: {self.pdf_path} (não é string)")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Caminho do PDF inválido: {self.pdf_path} (não é string)", color=ft.Colors.ERROR)))
            self.page.update()
            return False

        if not self.pdf_path.lower().endswith('.pdf'):
            logger.error(f"Arquivo não é PDF: {self.pdf_path}")
            self.page.open(ft.SnackBar(ft.Text(f"Erro: O arquivo {self.pdf_path} não é um PDF!", color=ft.Colors.ERROR)))
            self.page.update()
            return False

        if not os.path.exists(self.pdf_path):
            logger.error(f"Arquivo não encontrado: {self.pdf_path}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: O arquivo {self.pdf_path} não foi encontrado!", color=ft.Colors.ERROR)))
            self.page.update()
            return False

        try:
            with open(self.pdf_path, 'rb') as f:
                if os.path.getsize(self.pdf_path) == 0:
                    logger.warning(f"PDF vazio: {self.pdf_path}")
                    self.page.open(ft.SnackBar(ft.Text(f"Erro: O PDF {self.pdf_path} tá vazio!", color=ft.Colors.ERROR)))
                    self.page.update()
                    return False
            logger.info(f"Caminho do PDF validado com sucesso: {self.pdf_path}")
            return True
        except PermissionError as e:
            logger.error(f"Permissão negada ao abrir PDF: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Permissão negada ao abrir o PDF. Suporte: {e}", color=ft.Colors.ERROR)))
            self.page.update()
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao validar PDF: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Algo deu errado ao abrir o PDF. Suporte: {e}", color=ft.Colors.ERROR)))
            self.page.update()
            return False

    def extract_text_from_pdf(self) -> str:
        """Extrai texto do PDF com tratamento robusto."""
        logger.info(f"Extraindo texto do PDF: {self.pdf_path}")
        if not self.validate_pdf_path():
            logger.warning("Validação do caminho falhou, retornando vazio")
            return ""

        try:
            doc = pp.open(self.pdf_path)
            if doc.page_count == 0:
                logger.warning(f"PDF sem páginas: {self.pdf_path}")
                self.page.open(ft.SnackBar(ft.Text("Erro: Esse PDF tá vazio ou sem páginas!", color=ft.Colors.ERROR)))
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
                self.page.open(ft.SnackBar(ft.Text("Erro: Esse PDF não tem texto útil!", color=ft.Colors.ERROR)))
                self.page.update()
                return ""

            logger.info(f"Texto extraído com sucesso: {len(text)} caracteres")
            encrypted_text = encrypt(text, self.SECRET_KEY)
            logger.debug(f"Texto criptografado: {len(encrypted_text)} bytes")
            return encrypted_text
        except pp.PyMuPDFError as e:
            logger.error(f"Erro do PyMuPDF ao ler PDF: {e}")
            self.page.open(ft.SnackBar(ft.Text(f"Erro: Problema ao ler o PDF. Suporte: {e}", color=ft.Colors.ERROR)))
            self.page.update()
            return ""
        except Exception as e:
            logger.error(f"Erro inesperado ao extrair texto: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Algo deu errado ao extrair o texto. Suporte: {e}", color=ft.Colors.ERROR)))
            self.page.update()
            return ""

    def validate_extracted_text(self, text: str) -> bool:
        """Valida se o texto extraído é relevante pra inadimplência."""
        logger.info("Validando texto extraído")
        if not isinstance(text, str) or not text.strip():
            logger.warning("Texto extraído inválido ou vazio")
            return False

        try:
            decrypted_text = decrypt(text, self.SECRET_KEY)
            if not decrypted_text.strip():
                logger.warning("Texto descriptografado vazio")
                return False

            keywords = ["inadimplente", "inadimplência", "atraso", "renegociado", "vencimento", "dívida", "pendente"]
            financial_keywords = ["valor", "pagamento", "cliente", "cpf", "cnpj", "telefone"]

            has_main_keywords = any(keyword.lower() in decrypted_text.lower() for keyword in keywords)
            has_financial_context = any(keyword.lower() in decrypted_text.lower() for keyword in financial_keywords)

            if has_main_keywords and has_financial_context:
                logger.info("Texto validado como relatório de inadimplência")
                return True
            else:
                logger.warning("Texto não parece ser um relatório de inadimplência válido")
                self.page.open(ft.SnackBar(
                    ft.Text("Erro: Esse PDF não parece ser um relatório de inadimplência!", color=ft.Colors.ERROR)))
                self.page.update()
                return False
        except Exception as e:
            logger.error(f"Erro ao validar texto extraído: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Problema ao validar o texto extraído. Suporte: {e}", color=ft.Colors.ERROR)))
            self.page.update()
            return False

    def extract_clients_with_claude(self, text: str) -> List[dict]:
        logger.info("Iniciando extração com Claude")
        if not self.validate_extracted_text(text):
            logger.warning("Texto inválido pra extração, retornando vazio")
            return []

        try:
            decrypted_text = decrypt(text, self.SECRET_KEY)
            logger.debug(f"Texto descriptografado: {len(decrypted_text)} caracteres")

            # Divide o texto em pedaços com sobreposição pra não cortar tabelas
            chunk_size = self.MAX_TEXT_LENGTH
            overlap = 500  # Sobreposição pra garantir que linhas não sejam cortadas
            chunks = [decrypted_text[i:i + chunk_size] for i in range(0, len(decrypted_text), chunk_size - overlap)]
            clients_data = {}

            for i, chunk in enumerate(chunks):
                if "Nome" in chunk:  # Heurística pra achar tabela
                    logger.debug(f"Tabela possivelmente encontrada no chunk {i}: {len(chunk)} caracteres")
                    prompt = (
                        "You received a financial report in Portuguese. Identify tables or lists of pending clients. "
                        "Columns may include: Nome/Cliente (Name), CPF/CNPJ (ID), Valor/Dívida (Debt Amount), Vencimento/Data (Due Date), "
                        "Status/Situação (Status), Contato/Telefone (Contact). "
                        "Extract the data and return it as a JSON array with the fields: "
                        "id (CPF/CNPJ, remove spaces, dots, or dashes; if missing or empty, generate a temporary ID like 'TEMP_001', 'TEMP_002', etc.), "
                        "name (Nome/Cliente), debt_amount (Valor/Dívida, remove 'R$', convert to float), "
                        "due_date (Vencimento/Data, format DD/MM/YYYY; if invalid, set as 'PENDENTE'), "
                        "status (Status/Situação, e.g., 'Em atraso'), contact (Contato/Telefone, format (XX) XXXXX-XXXX). "
                        "Infer columns by context if labels are missing or different. "
                        "Keep lines with invalid dates by setting due_date to 'PENDENTE'. "
                        "Return the result as a JSON array in a Markdown block (```json ... ```). "
                        "If no valid data or table is found, return an empty array. "
                        f"{chunk}"
                    )
                    message = self.client.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=2000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response_text = message.content[0].text
                    logger.debug(f"Resposta do Claude recebida no chunk {i}: {len(response_text)} caracteres")
                    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)

                    if json_match:
                        try:
                            chunk_clients = json.loads(json_match.group(1))
                            if isinstance(chunk_clients, list):
                                for client in chunk_clients:
                                    # Usa ID + nome como chave pra evitar duplicatas
                                    client_key = f"{client['id']}_{client['name']}_{client['due_date']}"
                                    clients_data[client_key] = client
                                logger.info(f"Extraídos {len(chunk_clients)} clientes do chunk {i}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Erro ao parsear JSON do Claude no chunk {i}: {e}")
                            self.page.open(ft.SnackBar(
                                ft.Text(f"Erro: Problema ao interpretar o JSON do Claude no chunk {i}. Suporte: {e}", color=ft.Colors.RED)))

            clients_list = list(clients_data.values())
            if not clients_list:
                logger.info("Nenhum cliente extraído pelos chunks")
            else:
                logger.info(f"Total de {len(clients_list)} clientes extraídos dos chunks")
            return clients_list

        except anthropic.APIError as e:
            logger.error(f"Erro na API do Anthropic: {e}")
            self.page.open(ft.SnackBar(ft.Text(f"Erro: Problema na API do Claude. Suporte: {e}", color=ft.Colors.RED)))
            self.page.update()
            return []
        except Exception as e:
            logger.error(f"Erro inesperado ao extrair com Claude: {e}")
            self.page.open(ft.SnackBar(
                ft.Text(f"Erro: Algo deu errado ao extrair com Claude. Suporte: {e}", color=ft.Colors.RED)))
            self.page.update()
            return []

    def validate_client_data(self, client_data: dict) -> Optional[dict]:
        """Valida e sanitiza os dados de um cliente com suporte a IDs temporários e telefones fixos."""
        logger.info(f"Validando dados do cliente: {client_data}")
        required_fields = {"id", "name", "debt_amount", "due_date", "status", "contact"}
        if not isinstance(client_data, dict) or not all(field in client_data for field in required_fields):
            logger.warning(f"Dados de cliente inválidos ou incompletos: {client_data}")
            return None

        sanitized_data = {}

        # Validação do ID (CPF/CNPJ ou TEMP_XXX)
        id_str = str(client_data["id"]).replace(" ", "").replace(".", "").replace("-", "").replace("/", "")
        if id_str.startswith('TEMP_'):
            sanitized_data["id"] = id_str
            logger.info(f"ID temporário aceito: {id_str}")
        elif 11 <= len(id_str) <= 14 and id_str.isdigit():
            sanitized_data["id"] = id_str
        else:
            logger.warning(f"ID inválido: {id_str}")
            return None

        # Nome
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
        if due_date == "PENDENTE":
            sanitized_data["due_date"] = "PENDENTE"
            logger.warning(f"Data pendente para {name}: corrigir manualmente")
        else:
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
        formatted_contact = f"({contact_clean[:2]}) {contact_clean[2:6 if len(contact_clean) == 10 else 7]}-{contact_clean[6 if len(contact_clean) == 10 else 7:]}"
        sanitized_data["contact"] = formatted_contact
        # Checa se é celular (Twilio-compatible)
        if re.match(r'^\(\d{2}\) 9\d{4}-\d{4}$', formatted_contact):
            sanitized_data["twilio_compatible"] = True
            logger.info(f"Telefone celular detectado: {formatted_contact}")
        else:
            sanitized_data["twilio_compatible"] = False
            logger.warning(f"Telefone fixo detectado: {formatted_contact}")

        logger.info(f"Dados do cliente validados com sucesso: {sanitized_data}")
        return sanitized_data

    def extract_pending_data(self) -> List[PendingClient]:
        """Extrai dados de clientes pendentes com validação robusta."""
        logger.info(f"Iniciando extração de dados pendentes do PDF: {self.pdf_path}")
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
        if clients:
            pendentes = sum(1 for c in clients if c.due_date == "PENDENTE")
            if pendentes > 0:
                logger.info(f"{pendentes} clientes com data pendente")
        return clients
