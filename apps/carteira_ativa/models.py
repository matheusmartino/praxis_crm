"""
Módulo Carteira Ativa — models.

ContatoCarteira: histórico de interações com clientes ATIVOS.
Cada registro atualiza o campo data_ultimo_contato no Cliente correspondente
(feito pelo service registrar_contato, nunca diretamente aqui).
"""

from django.conf import settings
from django.db import models

from apps.core.enums import TipoInteracao
from apps.crm.models import Cliente


class ContatoCarteira(models.Model):
    """
    Registra cada interação realizada com um cliente ativo.

    Campos gerenciados pela view/service:
      - cliente     : cliente ATIVO que recebeu o contato
      - responsavel : usuário que realizou o contato
      - tipo        : canal usado (ligação, e-mail, WhatsApp, etc.)
      - observacao  : notas livres sobre o contato
      - proxima_acao_em : data sugerida para o próximo contato
      - criado_em   : timestamp automático (UTC, timezone-aware)
    """

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="contatos_carteira",
        verbose_name="Cliente",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contatos_carteira_registrados",
        verbose_name="Responsável",
    )
    # Reutiliza TipoInteracao já existente em core.enums
    # (LIGACAO, EMAIL, REUNIAO, WHATSAPP, VISITA)
    tipo = models.CharField(
        max_length=10,
        choices=TipoInteracao.choices,
        verbose_name="Tipo de contato",
    )
    observacao = models.TextField(blank=True, default="", verbose_name="Observação")
    proxima_acao_em = models.DateField(
        null=True, blank=True, verbose_name="Próxima ação em"
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Registrado em")

    class Meta:
        verbose_name = "Contato da Carteira"
        verbose_name_plural = "Contatos da Carteira"
        ordering = ["-criado_em"]

    def __str__(self):
        return (
            f"{self.get_tipo_display()} com {self.cliente} "
            f"— {self.criado_em:%d/%m/%Y}"
        )
