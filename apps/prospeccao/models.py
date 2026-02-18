import logging

from django.db import models
from django.utils import timezone

logger = logging.getLogger("praxis")


class StatusLead(models.TextChoices):
    NOVO = "NOVO", "Novo"
    EM_CONTATO = "EM_CONTATO", "Em contato"
    AGUARDANDO = "AGUARDANDO", "Aguardando"
    CONVERTIDO = "CONVERTIDO", "Convertido"
    PERDIDO = "PERDIDO", "Perdido"


class OrigemLead(models.TextChoices):
    GOOGLE = "GOOGLE", "Google"
    INSTAGRAM = "INSTAGRAM", "Instagram"
    FACEBOOK = "FACEBOOK", "Facebook"
    INDICACAO = "INDICACAO", "Indicação"
    WHATSAPP = "WHATSAPP", "WhatsApp"
    SITE = "SITE", "Site"
    LOJA_FISICA = "LOJA_FISICA", "Loja física"
    OUTRO = "OUTRO", "Outro"


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
    origem = models.CharField(
        max_length=100,
        choices=OrigemLead.choices,
        verbose_name="Origem",
    )
    produto_interesse = models.CharField(
        max_length=200, blank=True, default="", verbose_name="Produto de interesse"
    )
    status = models.CharField(
        max_length=10,
        choices=StatusLead.choices,
        default=StatusLead.NOVO,
        verbose_name="Status",
    )
    criado_por = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads_criados",
        verbose_name="Criado por",
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

    def converter(self):
        """Converte o lead em Cliente (idempotente).

        Regras:
            - Se já está CONVERTIDO, retorna None (não duplica).
            - Requer criado_por preenchido (para vincular empresa e criado_por ao Cliente).
            - Atualiza status para CONVERTIDO e preenche convertido_em.
            - Cria Cliente com status PROVISORIO na empresa do vendedor.
        """
        if self.convertido_em:
            return None

        if not self.criado_por:
            logger.warning(
                "Lead sem criado_por, conversao ignorada: lead_id=%s", self.pk,
            )
            return None

        from apps.crm.models import Cliente

        self.status = StatusLead.CONVERTIDO
        self.convertido_em = timezone.now()
        self.save(update_fields=["status", "convertido_em", "updated_at"])

        ue = getattr(self.criado_por, "usuario_empresa", None)
        empresa_nome = ue.empresa.nome if ue else ""

        cliente = Cliente.objects.create(
            nome=self.nome,
            telefone=self.telefone or "",
            email=self.email or "",
            criado_por=self.criado_por,
            nome_contato_principal=self.nome,
            telefone_contato=self.telefone or "",
            email_contato=self.email or "",
        )

        logger.info(
            "Lead convertido em Cliente: lead_id=%s cliente_id=%s empresa=%s",
            self.pk, cliente.pk, empresa_nome,
        )
        return cliente


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
