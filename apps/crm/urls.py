from django.urls import path

from apps.crm.views import ClienteCreateView, ClienteDetailView, ClienteListView

app_name = "crm"

urlpatterns = [
    path("clientes/", ClienteListView.as_view(), name="cliente_list"),
    path("clientes/novo/", ClienteCreateView.as_view(), name="cliente_create"),
    path("clientes/<int:pk>/", ClienteDetailView.as_view(), name="cliente_detail"),
]
