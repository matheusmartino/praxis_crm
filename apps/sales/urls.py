from django.urls import path

from apps.sales.views import (
    InteracaoCreateView,
    InteracaoListView,
    OportunidadeAvancarView,
    OportunidadeCreateView,
    OportunidadeDetailView,
    OportunidadeListView,
    OportunidadePerdidaView,
)

app_name = "sales"

urlpatterns = [
    path("oportunidades/", OportunidadeListView.as_view(), name="oportunidade_list"),
    path("oportunidades/nova/", OportunidadeCreateView.as_view(), name="oportunidade_create"),
    path("oportunidades/<int:pk>/", OportunidadeDetailView.as_view(), name="oportunidade_detail"),
    path("oportunidades/<int:pk>/avancar/", OportunidadeAvancarView.as_view(), name="oportunidade_avancar"),
    path("oportunidades/<int:pk>/perdida/", OportunidadePerdidaView.as_view(), name="oportunidade_perdida"),
    path("interacoes/", InteracaoListView.as_view(), name="interacao_list"),
    path("interacoes/nova/", InteracaoCreateView.as_view(), name="interacao_create"),
]
