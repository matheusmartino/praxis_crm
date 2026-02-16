from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from apps.core.mixins import VendedorRequiredMixin, VendedorWriteMixin
from apps.core.utils.query_scope import aplicar_escopo_usuario
from apps.crm.forms import ClienteForm
from apps.crm.models import Cliente
from apps.crm.services import criar_cliente


class ClienteListView(VendedorRequiredMixin, ListView):
    model = Cliente
    template_name = "crm/cliente_list.html"
    context_object_name = "clientes"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        qs = aplicar_escopo_usuario(qs, self.request.user, "criado_por")

        nome = self.request.GET.get("nome", "").strip()
        if nome:
            qs = qs.filter(nome__icontains=nome)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtro_nome"] = self.request.GET.get("nome", "")

        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_params"] = params.urlencode()

        return ctx


class ClienteCreateView(VendedorWriteMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "crm/cliente_form.html"
    success_url = reverse_lazy("crm:cliente_list")
    redirect_url_name = "crm:cliente_list"  # Redirecionamento para GESTOR

    def _buscar_duplicados(self, nome, cnpj_cpf):
        filtro = Q(nome__icontains=nome)
        if cnpj_cpf:
            filtro = filtro | Q(cnpj_cpf=cnpj_cpf)
        qs = aplicar_escopo_usuario(Cliente.objects.all(), self.request.user, "criado_por")
        return qs.filter(filtro)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)

        confirmar = request.POST.get("confirmar")
        if confirmar != "1":
            nome = form.cleaned_data["nome"]
            cnpj_cpf = form.cleaned_data.get("cnpj_cpf", "")
            duplicados = self._buscar_duplicados(nome, cnpj_cpf)
            if duplicados.exists():
                return render(request, self.template_name, {
                    "form": form,
                    "duplicados": duplicados,
                    "mostrar_confirmacao": True,
                })

        return self.form_valid(form)

    def form_valid(self, form):
        criar_cliente(
            nome=form.cleaned_data["nome"],
            telefone=form.cleaned_data["telefone"],
            email=form.cleaned_data["email"],
            tipo=form.cleaned_data["tipo"],
            user=self.request.user,
            cnpj_cpf=form.cleaned_data["cnpj_cpf"],
            nome_contato_principal=form.cleaned_data["nome_contato_principal"],
            telefone_contato=form.cleaned_data["telefone_contato"],
            email_contato=form.cleaned_data["email_contato"],
        )
        return redirect(self.success_url)


class ClienteDetailView(VendedorRequiredMixin, DetailView):
    model = Cliente
    template_name = "crm/cliente_detail.html"
    context_object_name = "cliente"

    def get_queryset(self):
        qs = super().get_queryset()
        return aplicar_escopo_usuario(qs, self.request.user, "criado_por")
