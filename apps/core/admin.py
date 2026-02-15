from django.contrib import admin

from apps.core.admin_mixins import GestorReadOnlyAdminMixin
from apps.core.models import Auditoria


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
