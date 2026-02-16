from django.contrib import admin

from apps.core.admin_mixins import GestorReadOnlyAdminMixin
from apps.prospeccao.models import ContatoLead, FollowUp, Lead


@admin.register(Lead)
class LeadAdmin(GestorReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "nome",
        "empresa",
        "telefone",
        "origem",
        "status",
        "created_at",
    )
    list_filter = ("status", "origem", "created_at")
    search_fields = ("nome", "empresa", "telefone", "email")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("nome", "empresa", "telefone", "whatsapp", "email"),
        }),
        ("Prospecção", {
            "fields": ("origem", "produto_interesse", "status", "observacoes"),
        }),
        ("Conversão", {
            "fields": ("convertido_em",),
        }),
        ("Auditoria", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(ContatoLead)
class ContatoLeadAdmin(GestorReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("lead", "tipo", "resultado", "data_contato")
    list_filter = ("tipo", "resultado", "data_contato")
    search_fields = ("lead__nome", "observacao")
    readonly_fields = ("created_at",)


@admin.register(FollowUp)
class FollowUpAdmin(GestorReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("lead", "data", "status", "descricao", "created_at")
    list_filter = ("status", "data")
    search_fields = ("lead__nome", "descricao")
    readonly_fields = ("created_at",)
