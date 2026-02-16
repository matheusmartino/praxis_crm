from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from apps.core.mixins import VendedorRequiredMixin, VendedorWriteMixin
from apps.prospeccao.forms import ContatoLeadForm, LeadForm
from apps.prospeccao.models import FollowUp, Lead, StatusFollowUp, StatusLead
from apps.prospeccao.services import registrar_contato


class LeadListView(VendedorRequiredMixin, ListView):
    model = Lead
    template_name = "prospeccao/lead_list.html"
    context_object_name = "leads"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
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

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = StatusLead.choices
        context["origens"] = (
            Lead.objects.values_list("origem", flat=True)
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


class LeadUpdateView(VendedorWriteMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "prospeccao/lead_form.html"
    success_url = reverse_lazy("prospeccao:lead_list")
    redirect_url_name = "prospeccao:lead_list"


class LeadDetailView(VendedorRequiredMixin, DetailView):
    model = Lead
    template_name = "prospeccao/lead_detail.html"
    context_object_name = "lead"

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
        self.lead = get_object_or_404(Lead, pk=self.kwargs["pk"])
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
        return (
            FollowUp.objects.filter(status=StatusFollowUp.PENDENTE, data__lte=hoje)
            .select_related("lead")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hoje"] = timezone.now().date()
        return context
