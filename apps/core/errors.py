"""
Handlers globais de erro HTTP.

Renderizam templates amigáveis sem expor stacktrace ao usuário final.
Cada erro é logado no nível apropriado para rastreabilidade.
"""

import logging

from django.shortcuts import render

logger = logging.getLogger("praxis.seguranca")


def handler403(request, exception=None):
    """Acesso negado — permissão insuficiente."""
    logger.warning(
        "403 Forbidden: user=%s path=%s ip=%s",
        getattr(request.user, "username", "anonymous"),
        request.path,
        _get_client_ip(request),
    )
    return render(request, "errors/403.html", status=403)


def handler404(request, exception=None):
    """Página não encontrada."""
    logger.info(
        "404 Not Found: path=%s ip=%s",
        request.path,
        _get_client_ip(request),
    )
    return render(request, "errors/404.html", status=404)


def handler500(request):
    """Erro interno do servidor."""
    logger.error(
        "500 Internal Server Error: user=%s path=%s method=%s ip=%s",
        getattr(request.user, "username", "anonymous"),
        request.path,
        request.method,
        _get_client_ip(request),
    )
    return render(request, "errors/500.html", status=500)


def _get_client_ip(request):
    """Extrai IP do cliente, respeitando proxy reverso (X-Forwarded-For)."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
