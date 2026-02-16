from django.db.models import Count, Q
from django.utils import timezone

from apps.core.utils.query_scope import aplicar_escopo_usuario
from apps.prospeccao.models import FollowUp, Lead, StatusFollowUp, StatusLead


def obter_metricas_prospeccao(user=None):
    """Retorna dict com todas as métricas do dashboard de prospecção."""
    totais = contar_leads_por_status(user=user)
    return {
        "total_leads": totais["total"],
        "leads_convertidos": totais["convertidos"],
        "leads_perdidos": totais["perdidos"],
        "taxa_conversao": calcular_taxa_conversao(
            totais["convertidos"], totais["perdidos"]
        ),
        "leads_por_origem": agrupar_leads_por_origem(user=user),
        "conversao_por_vendedor": calcular_conversao_por_vendedor(user=user),
        "followups_atrasados": listar_followups_atrasados(user=user),
        "total_followups_atrasados": contar_followups_atrasados(user=user),
    }


def _base_leads(user):
    """Retorna queryset base de leads com escopo aplicado."""
    qs = Lead.objects.all()
    if user is not None:
        qs = aplicar_escopo_usuario(qs, user, "criado_por")
    return qs


def _base_followups(user):
    """Retorna queryset base de follow-ups com escopo aplicado."""
    qs = FollowUp.objects.all()
    if user is not None:
        qs = aplicar_escopo_usuario(qs, user, "lead__criado_por")
    return qs


def contar_leads_por_status(user=None):
    """Conta total, convertidos e perdidos."""
    return _base_leads(user).aggregate(
        total=Count("id"),
        convertidos=Count("id", filter=Q(status=StatusLead.CONVERTIDO)),
        perdidos=Count("id", filter=Q(status=StatusLead.PERDIDO)),
    )


def calcular_taxa_conversao(convertidos, perdidos):
    """Taxa = convertidos / (convertidos + perdidos) * 100."""
    finalizados = convertidos + perdidos
    if finalizados == 0:
        return 0
    return round(convertidos / finalizados * 100, 1)


def agrupar_leads_por_origem(user=None):
    """Agrupa leads por origem com totais e taxas."""
    return (
        _base_leads(user)
        .values("origem")
        .annotate(
            total=Count("id"),
            convertidos=Count(
                "id", filter=Q(status=StatusLead.CONVERTIDO)
            ),
            perdidos=Count(
                "id", filter=Q(status=StatusLead.PERDIDO)
            ),
        )
        .order_by("-total")
    )


def calcular_conversao_por_vendedor(user=None):
    """Agrupa leads por criado_por (vendedor) com totais e taxas."""
    dados = (
        _base_leads(user)
        .filter(criado_por__isnull=False)
        .values("criado_por__first_name", "criado_por__last_name", "criado_por__username")
        .annotate(
            total=Count("id"),
            convertidos=Count(
                "id", filter=Q(status=StatusLead.CONVERTIDO)
            ),
            perdidos=Count(
                "id", filter=Q(status=StatusLead.PERDIDO)
            ),
        )
        .order_by("-total")
    )
    resultado = []
    for item in dados:
        nome = (
            f"{item['criado_por__first_name']} {item['criado_por__last_name']}".strip()
            or item["criado_por__username"]
        )
        finalizados = item["convertidos"] + item["perdidos"]
        taxa = round(item["convertidos"] / finalizados * 100, 1) if finalizados else 0
        resultado.append(
            {
                "vendedor": nome,
                "total": item["total"],
                "convertidos": item["convertidos"],
                "perdidos": item["perdidos"],
                "taxa": taxa,
            }
        )
    return resultado


def contar_followups_atrasados(user=None):
    """Conta follow-ups pendentes com data passada."""
    hoje = timezone.now().date()
    return _base_followups(user).filter(
        status=StatusFollowUp.PENDENTE, data__lt=hoje
    ).count()


def listar_followups_atrasados(user=None):
    """Lista follow-ups pendentes atrasados com dados do lead."""
    hoje = timezone.now().date()
    return (
        _base_followups(user)
        .filter(status=StatusFollowUp.PENDENTE, data__lt=hoje)
        .select_related("lead")
        .order_by("data")
    )
