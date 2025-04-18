class MessageTemplates:
    """Gerencia modelos de mensagens para notificações."""

    def __init__(self):
        self.templates = {
            "Padrão": "Olá {name}, notamos que o valor de {debt_amount} com vencimento em {due_date} está pendente. Entre em contato para mais detalhes!",
            "Gentil": "Oi {name}, tudo bem? Gostaríamos de lembrar que o valor de {debt_amount} vence em {due_date}. Podemos ajudar com algo?",
            "Informativo": "Prezado(a) {name}, informamos que o valor de {debt_amount} está programado para {due_date}. Qualquer dúvida, estamos à disposição!",
            "Aviso Formal": "Prezado(a) {name}, informamos que há uma pendência de {debt_amount}, vencida em {due_date}, referente a {reason}. Solicitamos a regularização até {due_date}. Entre em contato para mais detalhes.",
            "Último Aviso": "Atenção, {name}! Sua pendência de {debt_amount} (vencida em {due_date}) está em atraso. Regularize até {due_date} para evitar medidas adicionais. Contate-nos agora!",
            "Negociação": "Oi, {name}! Notamos uma pendência de {debt_amount} (vencimento: {due_date}). Que tal conversarmos? Podemos parcelar ou ajustar pra facilitar o pagamento. Responda pra negociar!",
            "Confirmação": "Olá, {name}! Estamos tentando contato sobre sua pendência de {debt_amount}, vencida em {due_date}. Confirme o recebimento ou regularize para evitar novas notificações.",
            "Desconto": "Boa notícia, {name}! Regularize sua pendência de {debt_amount} (vencida em {due_date}) até {due_date} e ganhe 10% de desconto. Aproveite!",
            "Renovação": "Ei, {name}! Sua pendência de {debt_amount} venceu em {due_date}. Renove seu plano ou regularize pra continuar aproveitando nossos serviços. Qualquer dúvida, é só chamar!"
        }
        self.selected_template = "Padrão"

    def get_template(self, name=None):
        """Retorna o modelo de mensagem especificado ou o selecionado."""
        return self.templates.get(name or self.selected_template, self.templates["Padrão"])

    def set_template(self, name):
        """Define o modelo de mensagem selecionado."""
        if name in self.templates:
            self.selected_template = name
