from django.contrib import admin

from apps.sales.models import Interacao, Oportunidade


class InteracaoInline(admin.TabularInline):
    model = Interacao
    extra = 0
    readonly_fields = ("criado_por", "criado_em")


@admin.register(Oportunidade)
class OportunidadeAdmin(admin.ModelAdmin):
    list_display = ("titulo", "cliente", "vendedor", "etapa", "valor_estimado", "criado_em")
    list_filter = ("etapa", "criado_em")
    search_fields = ("titulo", "cliente__nome")
    readonly_fields = ("criado_em", "atualizado_em")
    inlines = [InteracaoInline]


@admin.register(Interacao)
class InteracaoAdmin(admin.ModelAdmin):
    list_display = ("oportunidade", "tipo", "criado_por", "criado_em")
    list_filter = ("tipo", "criado_em")
    search_fields = ("descricao", "oportunidade__titulo")
    readonly_fields = ("criado_por", "criado_em")
