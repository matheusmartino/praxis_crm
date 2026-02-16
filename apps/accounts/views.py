from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.forms import LoginForm
from apps.core.enums import PerfilUsuario
from apps.core.utils.query_scope import aplicar_escopo_usuario
from apps.crm.models import Cliente
from apps.prospeccao.models import Lead
from apps.sales.models import Oportunidade


class LoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm


class LogoutView(auth_views.LogoutView):
    next_page = "/accounts/login/"


@login_required
def home_view(request):
    user = request.user

    # Gestor/Admin: redireciona para dashboard de gestão (evita dashboard vazio)
    if hasattr(user, "perfil") and user.perfil.papel in (
        PerfilUsuario.GESTOR,
        PerfilUsuario.ADMIN,
    ):
        return redirect("gestao:dashboard")

    clientes_recentes = aplicar_escopo_usuario(
        Cliente.objects.all(), user, "criado_por"
    ).order_by("-criado_em")[:5]
    oportunidades_abertas = aplicar_escopo_usuario(
        Oportunidade.objects.all(), user, "vendedor"
    ).exclude(etapa__in=["FECHAMENTO", "PERDIDA"])

    # Lembrete visual: oportunidades com follow-up para hoje e vencidos
    hoje = timezone.now().date()
    followups_hoje = oportunidades_abertas.filter(data_follow_up=hoje).count()

    total_leads = aplicar_escopo_usuario(
        Lead.objects.all(), user, "criado_por"
    ).count()

    context = {
        "clientes_recentes": clientes_recentes,
        "oportunidades_abertas": oportunidades_abertas,
        "total_oportunidades": oportunidades_abertas.count(),
        "followups_hoje": followups_hoje,
        "total_leads": total_leads,
    }
    return render(request, "home.html", context)


@login_required
def manual_view(request):
    """Exibe o manual do usuário."""
    manual_path = settings.BASE_DIR / "docs" / "manual_usuario.html"
    if not manual_path.exists():
        raise Http404("Manual não encontrado.")
    return FileResponse(open(manual_path, "rb"), content_type="text/html")


def landing_view(request):
    """Landing page institucional do Praxis CRM."""
    return render(request, "landing.html")
