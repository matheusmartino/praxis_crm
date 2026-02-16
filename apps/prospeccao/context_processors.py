from django.utils import timezone

from apps.core.utils.query_scope import aplicar_escopo_usuario
from apps.prospeccao.models import FollowUp, StatusFollowUp


def followups_pendentes(request):
    """Injeta contador de follow-ups pendentes (hoje + atrasados) em todos os templates."""
    if not request.user.is_authenticated:
        return {}

    hoje = timezone.now().date()
    qs = FollowUp.objects.filter(status=StatusFollowUp.PENDENTE, data__lte=hoje)
    total = aplicar_escopo_usuario(qs, request.user, "lead__criado_por").count()

    return {"total_followups_pendentes": total}
