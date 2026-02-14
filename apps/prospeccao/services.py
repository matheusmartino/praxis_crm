from django.utils import timezone

from apps.prospeccao.models import (
    ContatoLead,
    FollowUp,
    ResultadoContato,
    StatusFollowUp,
    StatusLead,
)


# Mapeamento: resultado do contato → novo status do lead.
# NAO_ATENDEU  → EM_CONTATO  (houve tentativa de contato)
# PEDIU_RETORNO → AGUARDANDO (lead pediu para retornar depois)
# INTERESSADO  → EM_CONTATO  (lead demonstrou interesse, negociação ativa)
# SEM_INTERESSE → PERDIDO    (lead não quer prosseguir)
# FECHOU       → CONVERTIDO  (lead virou cliente, preenche convertido_em)
RESULTADO_PARA_STATUS = {
    ResultadoContato.NAO_ATENDEU: StatusLead.EM_CONTATO,
    ResultadoContato.PEDIU_RETORNO: StatusLead.AGUARDANDO,
    ResultadoContato.INTERESSADO: StatusLead.EM_CONTATO,
    ResultadoContato.SEM_INTERESSE: StatusLead.PERDIDO,
    ResultadoContato.FECHOU: StatusLead.CONVERTIDO,
}


def registrar_contato(*, lead, tipo, resultado, observacao="", proximo_contato=None):
    """Registra um contato com o lead e atualiza seu status automaticamente.

    Se proximo_contato (date) for informado, cria um FollowUp PENDENTE
    e cancela follow-ups pendentes anteriores do mesmo lead.
    """
    contato = ContatoLead.objects.create(
        lead=lead,
        tipo=tipo,
        resultado=resultado,
        observacao=observacao,
    )

    # Atualiza status do lead conforme resultado do contato
    novo_status = RESULTADO_PARA_STATUS[resultado]
    lead.status = novo_status

    # Se fechou, registra data de conversão
    if resultado == ResultadoContato.FECHOU:
        lead.convertido_em = timezone.now()

    lead.save(update_fields=["status", "convertido_em", "updated_at"])

    # Cria follow-up se data do próximo contato foi informada
    if proximo_contato:
        # Cancela follow-ups pendentes anteriores deste lead
        FollowUp.objects.filter(
            lead=lead, status=StatusFollowUp.PENDENTE
        ).update(status=StatusFollowUp.CANCELADO)

        FollowUp.objects.create(
            lead=lead,
            data=proximo_contato,
            descricao=f"Retorno após: {contato.get_tipo_display()} - {contato.get_resultado_display()}",
        )

    return contato
