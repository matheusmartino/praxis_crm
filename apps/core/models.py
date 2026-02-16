from django.conf import settings
from django.db import models


class Auditoria(models.Model):
    """
    Registro de auditoria para ações relevantes no sistema.

    Cada entrada registra quem fez o quê, quando, e de onde.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias",
        verbose_name="Usuário",
    )
    acao = models.CharField("Ação", max_length=100, db_index=True)
    descricao = models.TextField("Descrição", blank=True, default="")
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.TextField("User-Agent", blank=True, default="")
    criado_em = models.DateTimeField("Criado em", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Auditoria"
        verbose_name_plural = "Auditorias"

    def __str__(self):
        user = self.usuario.username if self.usuario else "sistema"
        return f"[{self.criado_em:%Y-%m-%d %H:%M}] {user} — {self.acao}"
