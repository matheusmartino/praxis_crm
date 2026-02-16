from django.urls import path

from apps.prospeccao.views import (
    ContatoLeadCreateView,
    DashboardProspeccaoView,
    FollowUpHojeView,
    LeadCreateView,
    LeadDetailView,
    LeadListView,
    LeadUpdateView,
)

app_name = "prospeccao"

urlpatterns = [
    path("", LeadListView.as_view(), name="lead_list"),
    path("novo/", LeadCreateView.as_view(), name="lead_create"),
    path("dashboard/", DashboardProspeccaoView.as_view(), name="dashboard_prospeccao"),
    path("followups-hoje/", FollowUpHojeView.as_view(), name="followup_hoje"),
    path("<int:pk>/", LeadDetailView.as_view(), name="lead_detail"),
    path("<int:pk>/editar/", LeadUpdateView.as_view(), name="lead_update"),
    path("<int:pk>/registrar-contato/", ContatoLeadCreateView.as_view(), name="contato_create"),
]
