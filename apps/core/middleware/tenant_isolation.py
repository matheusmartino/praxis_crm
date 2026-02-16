"""
Middleware de isolamento de acesso (preparação para multi-tenancy).

No modelo atual (single-tenant, role-based), este middleware:
1. Injeta o perfil do usuário em request.perfil para acesso rápido
2. Loga tentativas de acesso sem perfil configurado

Quando houver evolução para multi-tenancy real, este middleware será
o ponto central para injetar o tenant e filtrar querysets globalmente.
"""

import logging

from apps.core.exceptions import TenantAccessDenied

logger = logging.getLogger("praxis.seguranca")


class TenantIsolationMiddleware:
    """Injeta perfil no request e valida integridade de acesso."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Injeta perfil no request para acesso rápido em views/services
        request.perfil = None

        if hasattr(request, "user") and request.user.is_authenticated:
            perfil = getattr(request.user, "perfil", None)
            if perfil:
                request.perfil = perfil
            else:
                # Usuário autenticado sem perfil — situação anômala
                logger.warning(
                    "Usuário autenticado sem perfil: user=%s ip=%s path=%s",
                    request.user.username,
                    _get_client_ip(request),
                    request.path,
                )

        return self.get_response(request)

    def process_exception(self, request, exception):
        """Loga tentativas de violação de isolamento."""
        if isinstance(exception, TenantAccessDenied):
            user = getattr(request, "user", None)
            username = getattr(user, "username", "anonymous") if user else "anonymous"

            logger.error(
                "Violação de isolamento: user=%s ip=%s path=%s method=%s — %s",
                username,
                _get_client_ip(request),
                request.path,
                request.method,
                str(exception),
            )

        # Retorna None — repropaga para handler403 (já é PermissionDenied)
        return None


def _get_client_ip(request):
    """Extrai IP do cliente, respeitando proxy reverso (X-Forwarded-For)."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
