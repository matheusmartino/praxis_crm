"""
Exceções customizadas do Praxis CRM.

Centralizadas aqui para reutilização em qualquer app.
"""

from django.core.exceptions import PermissionDenied


class TenantAccessDenied(PermissionDenied):
    """
    Acesso negado por violação de isolamento de dados.

    No modelo atual (role-based, single-tenant), sinaliza que um
    usuário tentou acessar dados fora do seu escopo de permissão.
    Preparado para evolução futura para multi-tenancy real.
    """

    pass
