from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from apps.accounts.models import Perfil
from apps.core.admin_mixins import GestorReadOnlyAdminMixin
from apps.core.models import UsuarioEmpresa


class PerfilInline(admin.StackedInline):
    model = Perfil
    fk_name = "user"
    can_delete = False
    verbose_name_plural = "Perfil"
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


class UsuarioEmpresaInline(admin.StackedInline):
    model = UsuarioEmpresa
    can_delete = False
    verbose_name_plural = "Empresa"
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


class UserAdmin(GestorReadOnlyAdminMixin, BaseUserAdmin):
    inlines = (PerfilInline, UsuarioEmpresaInline)

    def get_inlines(self, request, obj):
        if obj is None:
            return []
        return self.inlines


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
