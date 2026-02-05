from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.core.mixins import VendedorRequiredMixin
from apps.sales.forms import InteracaoForm, OportunidadeForm
from apps.sales.models import Interacao, Oportunidade
from apps.sales.services import avancar_etapa, criar_oportunidade, marcar_perdida, registrar_interacao


class OportunidadeListView(VendedorRequiredMixin, ListView):
    model = Oportunidade
    template_name = "sales/oportunidade_list.html"
    context_object_name = "oportunidades"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, "perfil") and self.request.user.perfil.is_vendedor:
            qs = qs.filter(vendedor=self.request.user)
        return qs


class OportunidadeCreateView(VendedorRequiredMixin, CreateView):
    model = Oportunidade
    form_class = OportunidadeForm
    template_name = "sales/oportunidade_form.html"
    success_url = reverse_lazy("sales:oportunidade_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if hasattr(self.request.user, "perfil") and self.request.user.perfil.is_vendedor:
            form.fields["cliente"].queryset = form.fields["cliente"].queryset.filter(
                criado_por=self.request.user
            )
        return form

    def form_valid(self, form):
        criar_oportunidade(
            titulo=form.cleaned_data["titulo"],
            cliente=form.cleaned_data["cliente"],
            vendedor=self.request.user,
            valor_estimado=form.cleaned_data["valor_estimado"],
            descricao=form.cleaned_data["descricao"],
        )
        return redirect(self.success_url)


class OportunidadeDetailView(VendedorRequiredMixin, DetailView):
    model = Oportunidade
    template_name = "sales/oportunidade_detail.html"
    context_object_name = "oportunidade"

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, "perfil") and self.request.user.perfil.is_vendedor:
            qs = qs.filter(vendedor=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["interacoes"] = self.object.interacoes.all()
        return ctx


class OportunidadeAvancarView(VendedorRequiredMixin, View):
    def post(self, request, pk):
        oportunidade = get_object_or_404(Oportunidade, pk=pk)
        if hasattr(request.user, "perfil") and request.user.perfil.is_vendedor:
            if oportunidade.vendedor != request.user:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
        avancar_etapa(oportunidade=oportunidade)
        return redirect("sales:oportunidade_detail", pk=pk)


class OportunidadePerdidaView(VendedorRequiredMixin, View):
    def post(self, request, pk):
        oportunidade = get_object_or_404(Oportunidade, pk=pk)
        if hasattr(request.user, "perfil") and request.user.perfil.is_vendedor:
            if oportunidade.vendedor != request.user:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
        marcar_perdida(oportunidade=oportunidade)
        return redirect("sales:oportunidade_detail", pk=pk)


class InteracaoListView(VendedorRequiredMixin, ListView):
    model = Interacao
    template_name = "sales/interacao_list.html"
    context_object_name = "interacoes"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, "perfil") and self.request.user.perfil.is_vendedor:
            qs = qs.filter(criado_por=self.request.user)
        return qs


class InteracaoCreateView(VendedorRequiredMixin, CreateView):
    model = Interacao
    form_class = InteracaoForm
    template_name = "sales/interacao_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if hasattr(self.request.user, "perfil") and self.request.user.perfil.is_vendedor:
            form.fields["oportunidade"].queryset = Oportunidade.objects.filter(
                vendedor=self.request.user
            )
        return form

    def form_valid(self, form):
        registrar_interacao(
            oportunidade=form.cleaned_data["oportunidade"],
            tipo=form.cleaned_data["tipo"],
            descricao=form.cleaned_data["descricao"],
            user=self.request.user,
        )
        return redirect("sales:interacao_list")
