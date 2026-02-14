from django.db import models
from django.utils import timezone


class StatusLead(models.TextChoices):
    NOVO = "NOVO", "Novo"
    EM_CONTATO = "EM_CONTATO", "Em contato"
    AGUARDANDO = "AGUARDANDO", "Aguardando"
    CONVERTIDO = "CONVERTIDO", "Convertido"
    PERDIDO = "PERDIDO", "Perdido"


class TipoContato(models.TextChoices):
    LIGACAO = "LIGACAO", "Ligação"
    WHATSAPP = "WHATSAPP", "WhatsApp"
    PRESENCIAL = "PRESENCIAL", "Presencial"
    EMAIL = "EMAIL", "E-mail"


class ResultadoContato(models.TextChoices):
    NAO_ATENDEU = "NAO_ATENDEU", "Não atendeu"
    SEM_INTERESSE = "SEM_INTERESSE", "Sem interesse"
    PEDIU_RETORNO = "PEDIU_RETORNO", "Pediu retorno"
    INTERESSADO = "INTERESSADO", "Interessado"
    FECHOU = "FECHOU", "Fechou"


class StatusFollowUp(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    CONCLUIDO = "CONCLUIDO", "Concluído"
    CANCELADO = "CANCELADO", "Cancelado"


class Lead(models.Model):
    """Representa um lead de prospecção (pré-CRM)."""

    nome = models.CharField(max_length=200, verbose_name="Nome")
    empresa = models.CharField(
        max_length=200, blank=True, default="", verbose_name="Empresa"
    )
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    whatsapp = models.CharField(
        max_length=20, blank=True, default="", verbose_name="WhatsApp"
    )
    email = models.EmailField(blank=True, default="", verbose_name="E-mail")
    origem = models.CharField(max_length=100, verbose_name="Origem")
    produto_interesse = models.CharField(
        max_length=200, blank=True, default="", verbose_name="Produto de interesse"
    )
    status = models.CharField(
        max_length=10,
        choices=StatusLead.choices,
        default=StatusLead.NOVO,
        verbose_name="Status",
    )
    observacoes = models.TextField(blank=True, default="", verbose_name="Observações")
    convertido_em = models.DateTimeField(
        null=True, blank=True, verbose_name="Convertido em"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ["-created_at"]

    def __str__(self):
        return self.nome


class ContatoLead(models.Model):
    """Registro de contato realizado com um lead (timeline de prospecção)."""

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="contatos",
        verbose_name="Lead",
    )
    tipo = models.CharField(
        max_length=11,
        choices=TipoContato.choices,
        verbose_name="Tipo de contato",
    )
    resultado = models.CharField(
        max_length=14,
        choices=ResultadoContato.choices,
        verbose_name="Resultado",
    )
    observacao = models.TextField(blank=True, default="", verbose_name="Observação")
    data_contato = models.DateTimeField(default=timezone.now, verbose_name="Data do contato")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Contato do Lead"
        verbose_name_plural = "Contatos do Lead"
        ordering = ["-data_contato"]

    def __str__(self):
        return f"{self.lead.nome} - {self.get_tipo_display()}"


class FollowUp(models.Model):
    """Lembrete de follow-up agendado para um lead."""

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="followups",
        verbose_name="Lead",
    )
    data = models.DateField(verbose_name="Data")
    descricao = models.CharField(
        max_length=200, blank=True, default="", verbose_name="Descrição"
    )
    status = models.CharField(
        max_length=9,
        choices=StatusFollowUp.choices,
        default=StatusFollowUp.PENDENTE,
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Follow-up"
        verbose_name_plural = "Follow-ups"
        ordering = ["data"]

    def __str__(self):
        return f"{self.lead.nome} - {self.data}"
