from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from apps.core.mixins import VendedorRequiredMixin, VendedorWriteMixin
from apps.prospeccao.forms import ContatoLeadForm, LeadForm
from apps.prospeccao.models import FollowUp, Lead, StatusFollowUp
from apps.prospeccao.services import registrar_contato


class LeadListView(VendedorRequiredMixin, ListView):
    model = Lead
    template_name = "prospeccao/lead_list.html"
    context_object_name = "leads"
    paginate_by = 20


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
