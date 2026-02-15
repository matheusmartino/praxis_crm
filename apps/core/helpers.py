"""Utilitários reutilizáveis do Praxis CRM."""

import logging

logger = logging.getLogger("praxis.auditoria")


def registrar_auditoria(request, acao, descricao=""):
    """
    Registra uma entrada de auditoria no banco e no log.

    Args:
        request: HttpRequest (para extrair user, IP, User-Agent).
        acao: Identificador curto da ação (ex: "lead.criar", "contato.registrar").
        descricao: Texto livre com detalhes adicionais.
    """
    from apps.core.models import Auditoria  # import local para evitar circular

    user = getattr(request, "user", None)
    if user and not user.is_authenticated:
        user = None

    ip = _get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    Auditoria.objects.create(
        usuario=user,
        acao=acao,
        descricao=descricao,
        ip=ip,
        user_agent=user_agent,
    )

    username = user.username if user else "anonymous"
    logger.info(
        "AUDITORIA: user=%s acao=%s ip=%s — %s",
        username,
        acao,
        ip,
        descricao or "(sem descrição)",
    )


def _get_client_ip(request):
    """Extrai IP do cliente, respeitando proxy reverso (X-Forwarded-For)."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
