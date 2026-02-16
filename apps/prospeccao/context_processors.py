from django.utils import timezone

from apps.prospeccao.models import FollowUp, StatusFollowUp


def followups_pendentes(request):
    """Injeta contador de follow-ups pendentes (hoje + atrasados) em todos os templates."""
    if not request.user.is_authenticated:
        return {}

    hoje = timezone.now().date()
    total = FollowUp.objects.filter(
        status=StatusFollowUp.PENDENTE, data__lte=hoje
    ).count()

    return {"total_followups_pendentes": total}
