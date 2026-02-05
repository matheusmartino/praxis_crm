from django.core.exceptions import ValidationError

from apps.core.enums import EtapaOportunidade
from apps.sales.models import Interacao, Oportunidade

ORDEM_ETAPAS = [
    EtapaOportunidade.PROSPECCAO,
    EtapaOportunidade.QUALIFICACAO,
    EtapaOportunidade.PROPOSTA,
    EtapaOportunidade.NEGOCIACAO,
    EtapaOportunidade.FECHAMENTO,
]


def criar_oportunidade(*, titulo, cliente, vendedor, valor_estimado=0, descricao=""):
    return Oportunidade.objects.create(
        titulo=titulo,
        cliente=cliente,
        vendedor=vendedor,
        valor_estimado=valor_estimado,
        descricao=descricao,
        etapa=EtapaOportunidade.PROSPECCAO,
    )


def avancar_etapa(*, oportunidade):
    """Avança a oportunidade para a próxima etapa do pipeline."""
    if oportunidade.etapa == EtapaOportunidade.PERDIDA:
        raise ValidationError("Oportunidade perdida não pode avançar.")

    if oportunidade.etapa == EtapaOportunidade.FECHAMENTO:
        raise ValidationError("Oportunidade já está na etapa final.")

    idx_atual = ORDEM_ETAPAS.index(oportunidade.etapa)
    oportunidade.etapa = ORDEM_ETAPAS[idx_atual + 1]
    oportunidade.save(update_fields=["etapa", "atualizado_em"])
    return oportunidade


def marcar_perdida(*, oportunidade):
    """Marca uma oportunidade como perdida."""
    if oportunidade.etapa == EtapaOportunidade.FECHAMENTO:
        raise ValidationError("Oportunidade fechada não pode ser marcada como perdida.")
    oportunidade.etapa = EtapaOportunidade.PERDIDA
    oportunidade.save(update_fields=["etapa", "atualizado_em"])
    return oportunidade


def registrar_interacao(*, oportunidade, tipo, descricao, user):
    return Interacao.objects.create(
        oportunidade=oportunidade,
        tipo=tipo,
        descricao=descricao,
        criado_por=user,
    )
