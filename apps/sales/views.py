from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from apps.core.mixins import GestorRequiredMixin, VendedorRequiredMixin, VendedorWriteMixin
from apps.core.utils.query_scope import aplicar_escopo_usuario
from apps.crm.models import Cliente
from apps.sales.models import Interacao, MetaComercial, Oportunidade
from apps.sales.forms import FollowUpForm, InteracaoForm, MotivoPerdaForm, OportunidadeForm
from apps.sales.services import (
    atualizar_follow_up,
    avancar_etapa,
    calcular_status_follow_up,
    criar_oportunidade,
    listar_metas_vendedores,
    listar_oportunidades_sem_follow_up,
    listar_pendencias_vendedor,
    marcar_perdida,
    obter_meta_vendedor,
    registrar_interacao,
)


class OportunidadeListView(VendedorRequiredMixin, ListView):
    model = Oportunidade
    template_name = "sales/oportunidade_list.html"
    context_object_name = "oportunidades"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        qs = aplicar_escopo_usuario(qs, self.request.user, "vendedor")

        cliente_id = self.request.GET.get("cliente")
        data_inicial = self.request.GET.get("data_inicial")
        data_final = self.request.GET.get("data_final")

        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        if data_inicial:
            qs = qs.filter(criado_em__date__gte=data_inicial)
        if data_final:
            qs = qs.filter(criado_em__date__lte=data_final)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["clientes"] = aplicar_escopo_usuario(
            Cliente.objects.all(), self.request.user, "criado_por"
        )

        ctx["filtro_cliente"] = self.request.GET.get("cliente", "")
        ctx["filtro_data_inicial"] = self.request.GET.get("data_inicial", "")
        ctx["filtro_data_final"] = self.request.GET.get("data_final", "")

        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_params"] = params.urlencode()

        return ctx


class OportunidadeCreateView(VendedorWriteMixin, CreateView):
    model = Oportunidade
    form_class = OportunidadeForm
    template_name = "sales/oportunidade_form.html"
    success_url = reverse_lazy("sales:oportunidade_list")
    redirect_url_name = "sales:oportunidade_list"  # Redirecionamento para GESTOR

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["cliente"].queryset = aplicar_escopo_usuario(
            form.fields["cliente"].queryset, self.request.user, "criado_por"
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
        return aplicar_escopo_usuario(qs, self.request.user, "vendedor")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["interacoes"] = self.object.interacoes.all()
        return ctx


class OportunidadeAvancarView(VendedorWriteMixin, View):
    redirect_url_name = "sales:oportunidade_list"  # Redirecionamento para GESTOR

    def post(self, request, pk):
        qs = aplicar_escopo_usuario(Oportunidade.objects.all(), request.user, "vendedor")
        oportunidade = get_object_or_404(qs, pk=pk)
        if hasattr(request.user, "perfil") and request.user.perfil.is_vendedor:
            if oportunidade.vendedor != request.user:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
        try:
            avancar_etapa(oportunidade=oportunidade)
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect("sales:oportunidade_detail", pk=pk)


class OportunidadePerdidaView(VendedorWriteMixin, View):
    redirect_url_name = "sales:oportunidade_list"  # Redirecionamento para GESTOR

    def _check_owner(self, request, oportunidade):
        if hasattr(request.user, "perfil") and request.user.perfil.is_vendedor:
            if oportunidade.vendedor != request.user:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied

    def _render(self, request, oportunidade, form):
        from django.shortcuts import render
        return render(request, "sales/oportunidade_perdida_form.html", {
            "oportunidade": oportunidade,
            "form": form,
        })

    def get(self, request, pk):
        qs = aplicar_escopo_usuario(Oportunidade.objects.all(), request.user, "vendedor")
        oportunidade = get_object_or_404(qs, pk=pk)
        self._check_owner(request, oportunidade)
        form = MotivoPerdaForm()
        return self._render(request, oportunidade, form)

    def post(self, request, pk):
        qs = aplicar_escopo_usuario(Oportunidade.objects.all(), request.user, "vendedor")
        oportunidade = get_object_or_404(qs, pk=pk)
        self._check_owner(request, oportunidade)
        form = MotivoPerdaForm(request.POST)
        if form.is_valid():
            try:
                marcar_perdida(
                    oportunidade=oportunidade,
                    motivo_perda=form.cleaned_data["motivo_perda"],
                )
                return redirect("sales:oportunidade_detail", pk=pk)
            except ValidationError as e:
                messages.error(request, e.message)
                return redirect("sales:oportunidade_detail", pk=pk)
        return self._render(request, oportunidade, form)


class InteracaoListView(VendedorRequiredMixin, ListView):
    model = Interacao
    template_name = "sales/interacao_list.html"
    context_object_name = "interacoes"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        qs = aplicar_escopo_usuario(qs, self.request.user, "criado_por")

        cliente_id = self.request.GET.get("cliente")
        data_inicial = self.request.GET.get("data_inicial")
        data_final = self.request.GET.get("data_final")

        if cliente_id:
            qs = qs.filter(oportunidade__cliente_id=cliente_id)
        if data_inicial:
            qs = qs.filter(criado_em__date__gte=data_inicial)
        if data_final:
            qs = qs.filter(criado_em__date__lte=data_final)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["clientes"] = aplicar_escopo_usuario(
            Cliente.objects.all(), self.request.user, "criado_por"
        )

        ctx["filtro_cliente"] = self.request.GET.get("cliente", "")
        ctx["filtro_data_inicial"] = self.request.GET.get("data_inicial", "")
        ctx["filtro_data_final"] = self.request.GET.get("data_final", "")

        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_params"] = params.urlencode()

        return ctx


class InteracaoCreateView(VendedorWriteMixin, CreateView):
    model = Interacao
    form_class = InteracaoForm
    template_name = "sales/interacao_form.html"
    redirect_url_name = "sales:interacao_list"  # Redirecionamento para GESTOR

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["oportunidade"].queryset = aplicar_escopo_usuario(
            Oportunidade.objects.all(), self.request.user, "vendedor"
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


# =============================================================================
# METAS COMERCIAIS
# =============================================================================


class MinhaMetaView(VendedorRequiredMixin, TemplateView):
    """
    View para o vendedor visualizar sua própria meta.
    Exibe: valor_meta, realizado, pipeline, percentual e status.
    """

    template_name = "sales/minha_meta.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtém mês/ano da query string ou usa atual
        mes = self.request.GET.get("mes")
        ano = self.request.GET.get("ano")

        if mes:
            mes = int(mes)
        if ano:
            ano = int(ano)

        dados = obter_meta_vendedor(
            vendedor=self.request.user,
            mes=mes,
            ano=ano,
        )

        context.update(dados)
        context["meses"] = MetaComercial.MESES
        context["ano_atual"] = timezone.now().year

        return context


class MetasPorVendedorView(GestorRequiredMixin, TemplateView):
    """
    View para gestor/admin visualizar metas de todos os vendedores.
    Exibe tabela com: vendedor, meta, realizado, pipeline, status.
    """

    template_name = "sales/metas_por_vendedor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtém mês/ano da query string ou usa atual
        mes = self.request.GET.get("mes")
        ano = self.request.GET.get("ano")

        if mes:
            mes = int(mes)
        if ano:
            ano = int(ano)

        metas, mes_atual, ano_atual = listar_metas_vendedores(
            mes=mes, ano=ano, user=self.request.user
        )

        context["metas"] = metas
        context["mes"] = mes_atual
        context["ano"] = ano_atual
        context["meses"] = MetaComercial.MESES
        context["ano_atual"] = timezone.now().year

        return context


# =============================================================================
# FOLLOW-UP E DISCIPLINA COMERCIAL
# =============================================================================


class MinhasPendenciasView(VendedorRequiredMixin, TemplateView):
    """
    View para o vendedor visualizar suas pendências de follow-up.
    Exibe oportunidades com follow-up atrasado ou para hoje.
    """

    template_name = "sales/minhas_pendencias.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Apenas VENDEDOR vê suas pendências
        if hasattr(self.request.user, "perfil") and self.request.user.perfil.is_vendedor:
            pendencias = listar_pendencias_vendedor(vendedor=self.request.user)
        else:
            pendencias = []

        context["pendencias"] = pendencias
        context["total_pendencias"] = len(pendencias)

        return context


class OportunidadesSemFollowUpView(GestorRequiredMixin, TemplateView):
    """
    View para gestor/admin visualizar oportunidades sem follow-up.
    Exibe oportunidades sem data de follow-up ou paradas há muitos dias.
    """

    template_name = "sales/oportunidades_sem_followup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtém parâmetro de dias da query string (default: 7)
        dias = self.request.GET.get("dias", 7)
        try:
            dias = int(dias)
        except ValueError:
            dias = 7

        oportunidades = listar_oportunidades_sem_follow_up(
            dias_parada=dias, user=self.request.user
        )

        context["oportunidades"] = oportunidades
        context["total"] = len(oportunidades)
        context["dias_filtro"] = dias

        return context


class FollowUpEditView(VendedorWriteMixin, View):
    """View para editar o follow-up de uma oportunidade."""

    redirect_url_name = "sales:oportunidade_list"

    def get(self, request, pk):
        qs = aplicar_escopo_usuario(Oportunidade.objects.all(), request.user, "vendedor")
        oportunidade = get_object_or_404(qs, pk=pk)

        # Verifica se é o dono da oportunidade (para VENDEDOR)
        if hasattr(request.user, "perfil") and request.user.perfil.is_vendedor:
            if oportunidade.vendedor != request.user:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied

        form = FollowUpForm(instance=oportunidade)
        return self._render(request, oportunidade, form)

    def post(self, request, pk):
        qs = aplicar_escopo_usuario(Oportunidade.objects.all(), request.user, "vendedor")
        oportunidade = get_object_or_404(qs, pk=pk)

        # Verifica se é o dono da oportunidade (para VENDEDOR)
        if hasattr(request.user, "perfil") and request.user.perfil.is_vendedor:
            if oportunidade.vendedor != request.user:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied

        form = FollowUpForm(request.POST, instance=oportunidade)
        if form.is_valid():
            atualizar_follow_up(
                oportunidade=oportunidade,
                proxima_acao=form.cleaned_data["proxima_acao"],
                data_follow_up=form.cleaned_data["data_follow_up"],
            )
            return redirect("sales:oportunidade_detail", pk=pk)

        return self._render(request, oportunidade, form)

    def _render(self, request, oportunidade, form):
        from django.shortcuts import render
        return render(request, "sales/followup_form.html", {
            "oportunidade": oportunidade,
            "form": form,
        })
