import logging

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
logger = logging.getLogger("praxis")

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

    # Se fechou, delega conversão ao método do model (cria Cliente)
    if resultado == ResultadoContato.FECHOU:
        lead.converter()
    else:
        lead.save(update_fields=["status", "updated_at"])

    logger.info(
        "Contato registrado: lead_id=%s tipo=%s resultado=%s novo_status=%s",
        lead.pk, tipo, resultado, novo_status,
    )

    # Cria follow-up se data do próximo contato foi informada
    if proximo_contato:
        # Cancela follow-ups pendentes anteriores deste lead
        cancelados = FollowUp.objects.filter(
            lead=lead, status=StatusFollowUp.PENDENTE
        ).update(status=StatusFollowUp.CANCELADO)

        if cancelados:
            logger.debug(
                "Follow-ups cancelados: lead_id=%s qtd=%s", lead.pk, cancelados,
            )

        FollowUp.objects.create(
            lead=lead,
            data=proximo_contato,
            descricao=f"Retorno após: {contato.get_tipo_display()} - {contato.get_resultado_display()}",
        )
        logger.info(
            "Follow-up criado: lead_id=%s data=%s", lead.pk, proximo_contato,
        )

    return contato
