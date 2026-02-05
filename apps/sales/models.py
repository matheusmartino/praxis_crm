from django.conf import settings
from django.db import models

from apps.core.enums import EtapaOportunidade, TipoInteracao
from apps.crm.models import Cliente


class Oportunidade(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="oportunidades",
        verbose_name="Cliente",
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="oportunidades",
        verbose_name="Vendedor",
    )
    etapa = models.CharField(
        max_length=12,
        choices=EtapaOportunidade.choices,
        default=EtapaOportunidade.PROSPECCAO,
        verbose_name="Etapa",
    )
    valor_estimado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Valor estimado",
    )
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Oportunidade"
        verbose_name_plural = "Oportunidades"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.titulo} — {self.cliente.nome}"


class Interacao(models.Model):
    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name="interacoes",
        verbose_name="Oportunidade",
    )
    tipo = models.CharField(
        max_length=10,
        choices=TipoInteracao.choices,
        verbose_name="Tipo",
    )
    descricao = models.TextField(verbose_name="Descrição")
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="interacoes",
        verbose_name="Criado por",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Interação"
        verbose_name_plural = "Interações"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.oportunidade.titulo}"
