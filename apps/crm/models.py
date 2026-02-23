from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.enums import StatusCliente, TipoCliente


class Cliente(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome")
    cnpj_cpf = models.CharField(
        max_length=18, blank=True, default="", verbose_name="CNPJ/CPF"
    )
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    nome_contato_principal = models.CharField(
        max_length=200, blank=True, default="", verbose_name="Contato principal"
    )
    telefone_contato = models.CharField(
        max_length=20, blank=True, default="", verbose_name="Telefone do contato"
    )
    email_contato = models.EmailField(
        blank=True, default="", verbose_name="E-mail do contato"
    )
    tipo = models.CharField(
        max_length=3,
        choices=TipoCliente.choices,
        default=TipoCliente.B2C,
        verbose_name="Tipo",
    )
    status = models.CharField(
        max_length=11,
        choices=StatusCliente.choices,
        default=StatusCliente.PROVISORIO,
        verbose_name="Status",
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clientes_criados",
        verbose_name="Criado por",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    # Preenchido automaticamente pelo módulo Carteira Ativa a cada contato registrado.
    # null → cliente nunca foi contatado (tratado como prioridade máxima na fila).
    data_ultimo_contato = models.DateTimeField(
        null=True, blank=True, verbose_name="Último contato"
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["-criado_em"]

    def clean(self):
        if self.status == StatusCliente.ATIVO and not self.cnpj_cpf:
            raise ValidationError(
                {"cnpj_cpf": "CNPJ/CPF é obrigatório para clientes ativos."}
            )

    def __str__(self):
        return self.nome
