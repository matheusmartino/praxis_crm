from django.contrib import admin

from apps.core.admin_mixins import GestorReadOnlyAdminMixin
from apps.core.models import Auditoria, Empresa, UsuarioEmpresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativa", "created_at")
    list_filter = ("ativa",)
    search_fields = ("nome",)


@admin.register(UsuarioEmpresa)
class UsuarioEmpresaAdmin(admin.ModelAdmin):
    list_display = ("user", "empresa")
    list_filter = ("empresa",)
    search_fields = ("user__username", "user__first_name", "empresa__nome")
    raw_id_fields = ("user",)


@admin.register(Auditoria)
class AuditoriaAdmin(GestorReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("criado_em", "usuario", "acao", "ip")
    list_filter = ("acao", "criado_em")
    search_fields = ("acao", "descricao", "usuario__username")
    readonly_fields = ("usuario", "acao", "descricao", "ip", "user_agent", "criado_em")
    date_hierarchy = "criado_em"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
