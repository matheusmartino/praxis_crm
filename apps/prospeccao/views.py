from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView,
)

from apps.core.enums import PerfilUsuario
from apps.core.mixins import GestorRequiredMixin, VendedorRequiredMixin, VendedorWriteMixin
from apps.core.utils.query_scope import aplicar_escopo_usuario
from apps.prospeccao.dashboard_service import obter_metricas_prospeccao
from apps.prospeccao.forms import ContatoLeadForm, LeadForm
from apps.prospeccao.models import FollowUp, Lead, StatusFollowUp, StatusLead
from apps.prospeccao.services import registrar_contato


class LeadListView(VendedorRequiredMixin, ListView):
    model = Lead
    template_name = "prospeccao/lead_list.html"
    context_object_name = "leads"
    paginate_by = 20
    

    def get_queryset(self):
        print("🔥 ENTROU NO GET_QUERYSET 🔥")
        qs = super().get_queryset()
        qs = aplicar_escopo_usuario(qs, self.request.user, "criado_por")

        nome = self.request.GET.get("nome", "").strip()
        status = self.request.GET.get("status", "").strip()
        origem = self.request.GET.get("origem", "").strip()
        data_inicio = self.request.GET.get("data_inicio", "").strip()
        data_fim = self.request.GET.get("data_fim", "").strip()

        if nome:
            qs = qs.filter(nome__icontains=nome)
        if status:
            qs = qs.filter(status=status)
        if origem:
            qs = qs.filter(origem__icontains=origem)
        if data_inicio:
            qs = qs.filter(created_at__date__gte=data_inicio)
        if data_fim:
            qs = qs.filter(created_at__date__lte=data_fim)

        return qs.exclude(status=StatusLead.CONVERTIDO)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = StatusLead.choices
        context["origens"] = (
            aplicar_escopo_usuario(Lead.objects.all(), self.request.user, "criado_por")
            .values_list("origem", flat=True)
            .distinct()
            .order_by("origem")
        )
        # Preserva filtros para o template
        context["filtros"] = {
            "nome": self.request.GET.get("nome", ""),
            "status": self.request.GET.get("status", ""),
            "origem": self.request.GET.get("origem", ""),
            "data_inicio": self.request.GET.get("data_inicio", ""),
            "data_fim": self.request.GET.get("data_fim", ""),
        }
        # Querystring sem page para links de paginação
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


class LeadCreateView(VendedorWriteMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "prospeccao/lead_form.html"
    success_url = reverse_lazy("prospeccao:lead_list")
    redirect_url_name = "prospeccao:lead_list"

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        return super().form_valid(form)


class LeadUpdateView(VendedorWriteMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "prospeccao/lead_form.html"
    success_url = reverse_lazy("prospeccao:lead_list")
    redirect_url_name = "prospeccao:lead_list"

    def get_queryset(self):
        print("get_queryset chamado para LeadUpdateView")
        qs = super().get_queryset()
        return aplicar_escopo_usuario(qs, self.request.user, "criado_por")

    def form_valid(self, form):
        print("form_valid chamado para LeadUpdateView")        
        status_anterior = Lead.objects.get(pk=self.object.pk).status
        response = super().form_valid(form)
        if status_anterior != StatusLead.CONVERTIDO and self.object.status == StatusLead.CONVERTIDO:
            self.object.converter()
        return response


class LeadDetailView(VendedorRequiredMixin, DetailView):
    model = Lead
    template_name = "prospeccao/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        qs = super().get_queryset()
        return aplicar_escopo_usuario(qs, self.request.user, "criado_por")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contatos"] = self.object.contatos.all()
        context["followups"] = self.object.followups.filter(
            status=StatusFollowUp.PENDENTE
        )
        return context


class ContatoLeadCreateView(VendedorWriteMixin, FormView):
    """Registra um contato com o lead e atualiza seu status via service."""

    template_name = "prospeccao/contato_form.html"
    form_class = ContatoLeadForm
    redirect_url_name = "prospeccao:lead_list"

    def dispatch(self, request, *args, **kwargs):
        qs = aplicar_escopo_usuario(Lead.objects.all(), request.user, "criado_por")
        self.lead = get_object_or_404(qs, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lead"] = self.lead
        return context

    def form_valid(self, form):
        registrar_contato(
            lead=self.lead,
            tipo=form.cleaned_data["tipo"],
            resultado=form.cleaned_data["resultado"],
            observacao=form.cleaned_data["observacao"],
            proximo_contato=form.cleaned_data.get("proximo_contato"),
        )
        return redirect("prospeccao:lead_detail", pk=self.lead.pk)


class FollowUpHojeView(VendedorRequiredMixin, ListView):
    """Lista follow-ups pendentes para hoje (e atrasados)."""

    model = FollowUp
    template_name = "prospeccao/followup_hoje.html"
    context_object_name = "followups"
    paginate_by = 20

    def get_queryset(self):
        hoje = timezone.now().date()
        qs = FollowUp.objects.filter(
            status=StatusFollowUp.PENDENTE, data__lte=hoje
        ).select_related("lead")
        return aplicar_escopo_usuario(qs, self.request.user, "lead__criado_por")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hoje"] = timezone.now().date()
        return context


class DashboardProspeccaoView(GestorRequiredMixin, TemplateView):
    template_name = "prospeccao/dashboard_prospeccao.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(obter_metricas_prospeccao(user=self.request.user))
        return context


class LeadDeleteView(GestorRequiredMixin, DeleteView):
    """Exclusão de Lead — apenas GESTOR/ADMIN, sem status CONVERTIDO e sem contatos."""

    model = Lead
    success_url = reverse_lazy("prospeccao:lead_list")

    def get_queryset(self):
        return aplicar_escopo_usuario(Lead.objects.all(), self.request.user, "criado_por")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        perfil = getattr(request.user, "perfil", None)
        if not perfil or perfil.papel not in (PerfilUsuario.GESTOR, PerfilUsuario.ADMIN):
            raise PermissionDenied

        qs = aplicar_escopo_usuario(Lead.objects.all(), request.user, "criado_por")
        lead = get_object_or_404(qs, pk=kwargs["pk"])

        if lead.status == StatusLead.CONVERTIDO:
            messages.error(request, "Não é possível excluir um lead já convertido.")
            return redirect("prospeccao:lead_detail", pk=lead.pk)

        if lead.contatos.exists():
            messages.error(request, "Não é possível excluir um lead com contatos registrados.")
            return redirect("prospeccao:lead_detail", pk=lead.pk)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Sem página de confirmação separada — exclusão via POST direto.
        return redirect("prospeccao:lead_detail", pk=self.kwargs["pk"])
