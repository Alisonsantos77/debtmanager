class MessageTemplates:
    """Gerencia modelos de mensagens para notificações."""

    def __init__(self):
        self.templates = {
            "Padrão": "Olá {name}, notamos que o valor de {debt_amount} com vencimento em {due_date} está pendente. Entre em contato para mais detalhes!",
            "Gentil": "Oi {name}, tudo bem? Gostaríamos de lembrar que o valor de {debt_amount} vence em {due_date}. Podemos ajudar com algo?",
            "Informativo": "Prezado(a) {name}, informamos que o valor de {debt_amount} está programado para {due_date}. Qualquer dúvida, estamos à disposição!"
        }
        self.selected_template = "Padrão"

    def get_template(self, name=None):
        """Retorna o modelo de mensagem especificado ou o selecionado."""
        return self.templates.get(name or self.selected_template, self.templates["Padrão"])

    def set_template(self, name):
        """Define o modelo de mensagem selecionado."""
        if name in self.templates:
            self.selected_template = name
