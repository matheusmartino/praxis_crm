from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from apps.core.enums import PerfilUsuario


class VendedorRequiredMixin(LoginRequiredMixin):
    """Permite acesso apenas a usuários com perfil VENDEDOR ou ADMIN."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(request.user, "perfil"):
            if request.user.perfil.papel in (
                PerfilUsuario.VENDEDOR,
                PerfilUsuario.ADMIN,
            ):
                return response
        raise PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin):
    """Permite acesso apenas a usuários com perfil ADMIN."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(request.user, "perfil"):
            if request.user.perfil.papel == PerfilUsuario.ADMIN:
                return response
        raise PermissionDenied
