from django.urls import path

from .views import (
    CarteiraDetailView,
    CarteiraListView,
    DashboardGestorView,
    FilaView,
    HistoricoView,
    RegistrarContatoView,
)

app_name = "carteira_ativa"

urlpatterns = [
    # ── Fila principal (nova view, Etapas 3-5) ───────────────────────────────
    path("", FilaView.as_view(), name="carteira_fila"),

    # ── Dashboard do Gestor ───────────────────────────────────────────────────
    path("dashboard/", DashboardGestorView.as_view(), name="carteira_dashboard"),

    # ── Etapa 1 — mantidas ───────────────────────────────────────────────────
    # Lista simples (sem semáforo) acessível via /carteira/lista/
    path("lista/", CarteiraListView.as_view(), name="carteira_list"),
    # Detalhe do cliente
    path("<int:pk>/", CarteiraDetailView.as_view(), name="carteira_detail"),

    # ── Ações sobre clientes ─────────────────────────────────────────────────
    # Registrar novo contato
    path(
        "cliente/<int:cliente_id>/contato/novo/",
        RegistrarContatoView.as_view(),
        name="registrar_contato",
    ),
    # Histórico de contatos (bônus)
    path(
        "cliente/<int:cliente_id>/historico/",
        HistoricoView.as_view(),
        name="historico",
    ),
]
