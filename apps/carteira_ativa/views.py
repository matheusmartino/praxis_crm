"""
Módulo Carteira Ativa — views.

Etapa 1 (mantidas sem alteração):
  CarteiraListView   → /carteira/lista/  lista simples de clientes ATIVOS
  CarteiraDetailView → /carteira/<pk>/   ficha do cliente

Etapa 3–5 (novas):
  FilaView             → /carteira/               fila com semáforo e ordenação
  RegistrarContatoView → /carteira/cliente/<id>/contato/novo/
  HistoricoView        → /carteira/cliente/<id>/historico/  (bônus)
"""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.core.enums import PerfilUsuario, TipoCliente
from apps.core.mixins import VendedorRequiredMixin
from apps.crm.models import Cliente

from .forms import ContatoCarteiraForm
from .models import ContatoCarteira
from .services import (
    listar_carteira,
    listar_fila,
    obter_cliente_ativo,
    obter_metricas_dashboard,
    registrar_contato,
)
from .utils import SEMAFORO_CONFIG, calcular_semaforo, dias_sem_contato

logger = logging.getLogger("praxis.carteira_ativa")

# ─── Opções de semáforo para o filtro do template ────────────────────────────
SEMAFORO_OPCOES = [
    ("", "Todos"),
    ("sem_contato", "Sem contato"),
    ("vermelho", "Crítico (41+ dias)"),
    ("amarelo", "Atenção (21–40 dias)"),
    ("verde", "Em dia (≤ 20 dias)"),
]


# ─── Etapa 1 — mantidas ──────────────────────────────────────────────────────

class CarteiraListView(VendedorRequiredMixin, ListView):
    """
    Lista paginada simples de clientes ATIVOS (Etapa 1, mantida).
    URL: /carteira/lista/
    """

    model = Cliente
    template_name = "carteira_ativa/carteira_list.html"
    context_object_name = "clientes"
    paginate_by = 20

    def get_queryset(self):
        nome = self.request.GET.get("nome", "").strip()
        tipo = self.request.GET.get("tipo", "").strip()
        return listar_carteira(self.request.user, nome=nome, tipo=tipo)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtro_nome"] = self.request.GET.get("nome", "")
        ctx["filtro_tipo"] = self.request.GET.get("tipo", "")
        ctx["tipo_choices"] = TipoCliente.choices
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_params"] = params.urlencode()
        return ctx


class CarteiraDetailView(VendedorRequiredMixin, DetailView):
    """
    Ficha completa de um cliente ATIVO (Etapa 1, mantida).
    URL: /carteira/<pk>/
    """

    model = Cliente
    template_name = "carteira_ativa/carteira_detail.html"
    context_object_name = "cliente"

    def get_object(self, queryset=None):
        return obter_cliente_ativo(self.kwargs["pk"], self.request.user)


# ─── Etapa 3 — Fila principal com semáforo ───────────────────────────────────

class FilaView(VendedorRequiredMixin, ListView):
    """
    Fila de contato: clientes ATIVOS ordenados por urgência do semáforo.

    Ordenação: sem contato → mais antigo → mais recente.
    Filtros GET disponíveis:
      ?q=<nome>                → busca parcial por nome
      ?tipo=B2B|B2C            → filtro por tipo de cliente
      ?s=verde|amarelo|vermelho|sem_contato → filtro por estado do semáforo

    Cada item da lista inclui semáforo calculado em Python
    para evitar queries complexas no banco.
    """

    model = Cliente
    template_name = "carteira_ativa/fila.html"
    context_object_name = "clientes"
    paginate_by = 25

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        tipo = self.request.GET.get("tipo", "").strip()
        semaforo = self.request.GET.get("s", "").strip()
        return listar_fila(self.request.user, nome=q, tipo=tipo, semaforo=semaforo)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Enriquece cada cliente da página atual com dados de semáforo.
        # Calculado em Python (não no DB) para manter a query simples.
        clientes_enriquecidos = []
        for c in ctx["clientes"]:
            sem = calcular_semaforo(c.data_ultimo_contato)
            clientes_enriquecidos.append({
                "obj": c,
                "semaforo": sem,
                "semaforo_cfg": SEMAFORO_CONFIG[sem],
                "dias": dias_sem_contato(c.data_ultimo_contato),
            })
        ctx["clientes_enriquecidos"] = clientes_enriquecidos

        # Filtros atuais (para re-popular o form e preservar na paginação)
        ctx["filtro_q"] = self.request.GET.get("q", "")
        ctx["filtro_tipo"] = self.request.GET.get("tipo", "")
        ctx["filtro_s"] = self.request.GET.get("s", "")
        ctx["tipo_choices"] = TipoCliente.choices
        ctx["semaforo_opcoes"] = SEMAFORO_OPCOES

        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_params"] = params.urlencode()

        return ctx


# ─── Etapa 5 — Registrar contato ─────────────────────────────────────────────

class RegistrarContatoView(VendedorRequiredMixin, View):
    """
    GET : exibe o formulário de novo contato para o cliente.
    POST: valida, chama registrar_contato() e redireciona para a fila.

    Segurança:
      - obter_cliente_ativo() garante que o cliente é ATIVO e está no escopo
        do usuário (vendedor vê só os seus; gestor/admin vê todos da empresa).
      - Um vendedor tentando acessar cliente de outro vendedor recebe 404.
    """

    template_name = "carteira_ativa/registrar_contato.html"

    def _get_cliente(self, cliente_id: int) -> Cliente:
        """Recupera o cliente com validação de escopo — lança 404 se inválido."""
        return obter_cliente_ativo(cliente_id, self.request.user)

    def get(self, request, cliente_id: int):
        cliente = self._get_cliente(cliente_id)
        form = ContatoCarteiraForm()
        return render(request, self.template_name, {"form": form, "cliente": cliente})

    def post(self, request, cliente_id: int):
        cliente = self._get_cliente(cliente_id)
        form = ContatoCarteiraForm(request.POST)

        if not form.is_valid():
            return render(
                request, self.template_name, {"form": form, "cliente": cliente}
            )

        registrar_contato(
            cliente=cliente,
            usuario=request.user,
            tipo=form.cleaned_data["tipo"],
            observacao=form.cleaned_data.get("observacao", ""),
            proxima_acao_em=form.cleaned_data.get("proxima_acao_em"),
        )

        messages.success(
            request,
            f"Contato com <strong>{cliente.nome}</strong> registrado com sucesso.",
        )
        return redirect("carteira_ativa:carteira_fila")


# ─── Bônus — Histórico de contatos ───────────────────────────────────────────

class HistoricoView(VendedorRequiredMixin, DetailView):
    """
    Lista os últimos contatos registrados para um cliente específico.
    URL: /carteira/cliente/<cliente_id>/historico/

    Usa obter_cliente_ativo() para garantir que só clientes ATIVOS
    do escopo do usuário sejam acessados.
    """

    model = Cliente
    template_name = "carteira_ativa/historico.html"
    context_object_name = "cliente"

    def get_object(self, queryset=None):
        return obter_cliente_ativo(self.kwargs["cliente_id"], self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Busca os 50 contatos mais recentes para não sobrecarregar a página
        ctx["contatos"] = (
            ContatoCarteira.objects.filter(cliente=self.object)
            .select_related("responsavel")
            .order_by("-criado_em")[:50]
        )
        return ctx


# ─── Dashboard do Gestor ──────────────────────────────────────────────────────

class DashboardGestorView(LoginRequiredMixin, TemplateView):
    """
    Dashboard de métricas da Carteira Ativa para GESTOR e ADMIN.
    URL: /carteira/dashboard/

    Controle de acesso:
      - GESTOR e ADMIN: acesso permitido
      - VENDEDOR ou sem perfil: Http404 silencioso
        (mesmo padrão de obter_cliente_ativo — não vaza informação com 403)

    Contexto disponível no template:
      kpis         – dict com total, sem_contato, verde, amarelo, vermelho
      por_vendedor – lista de dicts com subtotais por vendedor
      contatos_30d – lista de dicts com contatos nos últimos 30 dias
      tocados_7d   – int: clientes contatados nos últimos 7 dias
    """

    template_name = "carteira_ativa/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        # Autenticação padrão via LoginRequiredMixin
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Verifica papel — Http404 para VENDEDOR (comportamento silencioso)
        perfil = getattr(request.user, "perfil", None)
        if not perfil or perfil.papel not in (
            PerfilUsuario.GESTOR,
            PerfilUsuario.ADMIN,
        ):
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Todas as métricas são calculadas no banco (sem loops Python pesados)
        ctx.update(obter_metricas_dashboard(self.request.user))
        return ctx
