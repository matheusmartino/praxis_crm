import logging
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from django.utils import timezone

from apps.core.enums import EtapaOportunidade
from apps.core.utils.query_scope import aplicar_escopo_usuario
from apps.sales.models import HistoricoEtapa, Interacao, MetaComercial, Oportunidade

logger = logging.getLogger("praxis")

ORDEM_ETAPAS = [
    EtapaOportunidade.PROSPECCAO,
    EtapaOportunidade.QUALIFICACAO,
    EtapaOportunidade.PROPOSTA,
    EtapaOportunidade.NEGOCIACAO,
    EtapaOportunidade.FECHAMENTO,
]


def criar_oportunidade(*, titulo, cliente, vendedor, valor_estimado=0, descricao=""):
    oportunidade = Oportunidade.objects.create(
        titulo=titulo,
        cliente=cliente,
        vendedor=vendedor,
        valor_estimado=valor_estimado,
        descricao=descricao,
        etapa=EtapaOportunidade.PROSPECCAO,
    )
    logger.info(
        "Oportunidade criada: id=%s titulo=%s vendedor=%s",
        oportunidade.pk, titulo, vendedor.username,
    )
    return oportunidade


def avancar_etapa(*, oportunidade):
    """Avança a oportunidade para a próxima etapa do pipeline."""
    if oportunidade.etapa == EtapaOportunidade.PERDIDA:
        raise ValidationError("Oportunidade perdida não pode avançar.")

    if oportunidade.etapa == EtapaOportunidade.FECHAMENTO:
        raise ValidationError("Oportunidade já está na etapa final.")

    etapa_anterior = oportunidade.etapa
    idx_atual = ORDEM_ETAPAS.index(oportunidade.etapa)
    oportunidade.etapa = ORDEM_ETAPAS[idx_atual + 1]
    oportunidade.save(update_fields=["etapa", "atualizado_em"])
    logger.info(
        "Etapa avançada: oportunidade_id=%s de=%s para=%s",
        oportunidade.pk, etapa_anterior, oportunidade.etapa,
    )
    return oportunidade


def marcar_perdida(*, oportunidade, motivo_perda=""):
    """Marca uma oportunidade como perdida."""
    if oportunidade.etapa == EtapaOportunidade.FECHAMENTO:
        raise ValidationError("Oportunidade fechada não pode ser marcada como perdida.")
    etapa_anterior = oportunidade.etapa
    oportunidade.etapa = EtapaOportunidade.PERDIDA
    oportunidade.save(update_fields=["etapa", "atualizado_em"])
    logger.info(
        "Oportunidade perdida: id=%s etapa_anterior=%s",
        oportunidade.pk, etapa_anterior,
    )
    return oportunidade


def registrar_interacao(*, oportunidade, tipo, descricao, user):
    interacao = Interacao.objects.create(
        oportunidade=oportunidade,
        tipo=tipo,
        descricao=descricao,
        criado_por=user,
    )
    logger.info(
        "Interação registrada: oportunidade_id=%s tipo=%s user=%s",
        oportunidade.pk, tipo, user.username,
    )
    return interacao


# =============================================================================
# METAS COMERCIAIS
# =============================================================================


def calcular_realizado(*, vendedor, mes, ano):
    """
    Calcula o valor realizado (vendas fechadas) de um vendedor no mês/ano.
    Realizado = soma de valor_estimado das oportunidades com etapa FECHAMENTO.
    """
    total = Oportunidade.objects.filter(
        vendedor=vendedor,
        etapa=EtapaOportunidade.FECHAMENTO,
        atualizado_em__month=mes,
        atualizado_em__year=ano,
    ).aggregate(total=Sum("valor_estimado"))["total"]

    return total or Decimal("0.00")


def calcular_pipeline(*, vendedor, mes, ano):
    """
    Calcula o valor em pipeline (oportunidades abertas) de um vendedor no mês/ano.
    Pipeline = soma de valor_estimado das oportunidades que NÃO são FECHAMENTO nem PERDIDA.
    """
    total = Oportunidade.objects.filter(
        vendedor=vendedor,
        criado_em__month=mes,
        criado_em__year=ano,
    ).exclude(
        etapa__in=[EtapaOportunidade.FECHAMENTO, EtapaOportunidade.PERDIDA]
    ).aggregate(total=Sum("valor_estimado"))["total"]

    return total or Decimal("0.00")


def calcular_status_meta(*, valor_meta, pipeline):
    """
    Calcula o status da meta baseado no pipeline.
    - OK: pipeline >= 1.5 × valor_meta
    - ATENCAO: pipeline >= valor_meta
    - RISCO: pipeline < valor_meta
    """
    if valor_meta <= 0:
        return "OK"

    if pipeline >= valor_meta * Decimal("1.5"):
        return "OK"
    elif pipeline >= valor_meta:
        return "ATENCAO"
    else:
        return "RISCO"


def obter_meta_vendedor(*, vendedor, mes=None, ano=None):
    """
    Obtém a meta do vendedor para o mês/ano especificado.
    Se não informado, usa o mês/ano atual.
    Retorna dict com meta, realizado, pipeline, percentual e status.
    """
    if mes is None or ano is None:
        hoje = timezone.now()
        mes = mes or hoje.month
        ano = ano or hoje.year

    try:
        meta = MetaComercial.objects.get(vendedor=vendedor, mes=mes, ano=ano)
        valor_meta = meta.valor_meta
    except MetaComercial.DoesNotExist:
        meta = None
        valor_meta = Decimal("0.00")

    realizado = calcular_realizado(vendedor=vendedor, mes=mes, ano=ano)
    pipeline = calcular_pipeline(vendedor=vendedor, mes=mes, ano=ano)

    if valor_meta > 0:
        percentual = round((realizado / valor_meta) * 100, 1)
    else:
        percentual = Decimal("0.0")

    status = calcular_status_meta(valor_meta=valor_meta, pipeline=pipeline)

    return {
        "meta": meta,
        "valor_meta": valor_meta,
        "realizado": realizado,
        "pipeline": pipeline,
        "percentual": percentual,
        "status": status,
        "mes": mes,
        "ano": ano,
    }


def listar_metas_vendedores(*, mes=None, ano=None, user=None):
    """
    Lista todas as metas do mês/ano com os cálculos de cada vendedor.
    Usado pela visão do gestor.
    """
    if mes is None or ano is None:
        hoje = timezone.now()
        mes = mes or hoje.month
        ano = ano or hoje.year

    qs = MetaComercial.objects.filter(mes=mes, ano=ano).select_related("vendedor")
    if user is not None:
        qs = aplicar_escopo_usuario(qs, user, "vendedor")
    resultado = []

    for meta in qs:
        dados = obter_meta_vendedor(vendedor=meta.vendedor, mes=mes, ano=ano)
        resultado.append(dados)

    return resultado, mes, ano


# =============================================================================
# FOLLOW-UP E DISCIPLINA COMERCIAL
# =============================================================================


def calcular_status_follow_up(data_follow_up):
    """
    Calcula o status do follow-up baseado na data.
    - EM_DIA: data_follow_up > hoje
    - HOJE: data_follow_up == hoje
    - ATRASADO: data_follow_up < hoje
    - SEM_DATA: data_follow_up é None
    """
    if data_follow_up is None:
        return "SEM_DATA"

    hoje = timezone.now().date()

    if data_follow_up > hoje:
        return "EM_DIA"
    elif data_follow_up == hoje:
        return "HOJE"
    else:
        return "ATRASADO"


def calcular_dias_atraso(data_follow_up):
    """Calcula quantos dias de atraso (negativo se no futuro)."""
    if data_follow_up is None:
        return None

    hoje = timezone.now().date()
    diferenca = (hoje - data_follow_up).days
    return diferenca


def listar_pendencias_vendedor(*, vendedor):
    """
    Lista oportunidades do vendedor com follow-up atrasado ou para hoje.
    Retorna lista ordenada por mais atrasadas primeiro.
    """
    hoje = timezone.now().date()

    oportunidades = Oportunidade.objects.filter(
        vendedor=vendedor,
        data_follow_up__lte=hoje,
    ).exclude(
        etapa__in=[EtapaOportunidade.FECHAMENTO, EtapaOportunidade.PERDIDA]
    ).select_related("cliente").order_by("data_follow_up")

    resultado = []
    for oportunidade in oportunidades:
        dias_atraso = calcular_dias_atraso(oportunidade.data_follow_up)
        status = calcular_status_follow_up(oportunidade.data_follow_up)
        resultado.append({
            "oportunidade": oportunidade,
            "dias_atraso": dias_atraso,
            "status": status,
        })

    return resultado


def listar_oportunidades_sem_follow_up(*, dias_parada=7, user=None):
    """
    Lista oportunidades sem follow-up OU paradas há mais de X dias.
    Usado pela visão do gestor.
    """
    hoje = timezone.now()
    data_limite = hoje - timedelta(days=dias_parada)

    # Oportunidades abertas (excluindo fechadas e perdidas)
    oportunidades_abertas = Oportunidade.objects.exclude(
        etapa__in=[EtapaOportunidade.FECHAMENTO, EtapaOportunidade.PERDIDA]
    ).select_related("cliente", "vendedor")
    if user is not None:
        oportunidades_abertas = aplicar_escopo_usuario(
            oportunidades_abertas, user, "vendedor"
        )

    # Filtrar: sem data_follow_up OU sem movimentação há X dias
    oportunidades = oportunidades_abertas.filter(
        data_follow_up__isnull=True
    ) | oportunidades_abertas.filter(
        atualizado_em__lt=data_limite
    )

    # Remover duplicatas e ordenar
    oportunidades = oportunidades.distinct().order_by("atualizado_em")

    resultado = []
    for oportunidade in oportunidades:
        dias_sem_movimentacao = (hoje.date() - oportunidade.atualizado_em.date()).days
        tem_follow_up = oportunidade.data_follow_up is not None
        resultado.append({
            "oportunidade": oportunidade,
            "dias_sem_movimentacao": dias_sem_movimentacao,
            "tem_follow_up": tem_follow_up,
        })

    return resultado


def atualizar_follow_up(*, oportunidade, proxima_acao, data_follow_up):
    """Atualiza os campos de follow-up de uma oportunidade."""
    oportunidade.proxima_acao = proxima_acao or ""
    oportunidade.data_follow_up = data_follow_up
    oportunidade.save(update_fields=["proxima_acao", "data_follow_up", "atualizado_em"])
    logger.info(
        "Follow-up atualizado: oportunidade_id=%s data=%s",
        oportunidade.pk, data_follow_up,
    )
    return oportunidade


# =============================================================================
# LEMBRETES E ALERTAS
# =============================================================================


def contar_followups_hoje(*, vendedor):
    """
    Conta quantas oportunidades do vendedor têm follow-up para hoje.
    Usado para lembrete visual no dashboard.
    """
    hoje = timezone.now().date()
    return Oportunidade.objects.filter(
        vendedor=vendedor,
        data_follow_up=hoje,
    ).exclude(
        etapa__in=[EtapaOportunidade.FECHAMENTO, EtapaOportunidade.PERDIDA]
    ).count()


def contar_oportunidades_alerta(*, dias_parada=7, user=None):
    """
    Conta oportunidades sem follow-up ou paradas há mais de X dias.
    Usado para alerta visual no dashboard do gestor.
    Retorna dict com contagens separadas.
    """
    hoje = timezone.now()
    data_limite = hoje - timedelta(days=dias_parada)

    oportunidades_abertas = Oportunidade.objects.exclude(
        etapa__in=[EtapaOportunidade.FECHAMENTO, EtapaOportunidade.PERDIDA]
    )
    if user is not None:
        oportunidades_abertas = aplicar_escopo_usuario(
            oportunidades_abertas, user, "vendedor"
        )

    sem_followup = oportunidades_abertas.filter(data_follow_up__isnull=True).count()
    paradas = oportunidades_abertas.filter(atualizado_em__lt=data_limite).count()

    return {
        "sem_followup": sem_followup,
        "paradas": paradas,
        "total": sem_followup + paradas,
    }


# =============================================================================
# INSIGHTS DE GESTÃO (ETAPA 6)
# =============================================================================


def calcular_tempo_medio_etapas(user=None):
    """
    Calcula o tempo médio (em dias) que as oportunidades ficam em cada etapa.
    Compatível com SQLite (sem funções de janela).
    """
    from collections import defaultdict

    qs = HistoricoEtapa.objects.all()
    if user is not None:
        qs = aplicar_escopo_usuario(qs, user, "oportunidade__vendedor")
    oportunidade_ids = (
        qs.values_list("oportunidade_id", flat=True).distinct()
    )

    tempos_por_etapa = defaultdict(list)

    for op_id in oportunidade_ids:
        registros = list(
            HistoricoEtapa.objects.filter(oportunidade_id=op_id).order_by("data_mudanca")
        )
        for i, registro in enumerate(registros):
            if registro.etapa_nova == EtapaOportunidade.PERDIDA:
                continue
            if i + 1 < len(registros):
                dias = (registros[i + 1].data_mudanca - registro.data_mudanca).total_seconds() / 86400
            else:
                dias = (timezone.now() - registro.data_mudanca).total_seconds() / 86400
            tempos_por_etapa[registro.etapa_nova].append(dias)

    resultado = []
    for etapa_code, etapa_label in EtapaOportunidade.choices:
        if etapa_code == EtapaOportunidade.PERDIDA:
            continue
        tempos = tempos_por_etapa.get(etapa_code, [])
        if tempos:
            resultado.append({
                "etapa": etapa_label,
                "dias_medio": round(sum(tempos) / len(tempos), 1),
                "total_registros": len(tempos),
            })
        else:
            resultado.append({
                "etapa": etapa_label,
                "dias_medio": 0,
                "total_registros": 0,
            })

    return resultado


def calcular_insights_gestao(user=None):
    """
    Calcula três insights para o dashboard do gestor:
    1. Etapa com mais perdas
    2. Cobertura pipeline vs meta
    3. Dias médio parado (oportunidades abertas)
    """
    from collections import Counter

    # 1. Etapa com mais perdas
    qs_hist = HistoricoEtapa.objects.filter(
        etapa_nova=EtapaOportunidade.PERDIDA
    )
    if user is not None:
        qs_hist = aplicar_escopo_usuario(qs_hist, user, "oportunidade__vendedor")
    perdas = qs_hist.values_list("etapa_anterior", flat=True)
    perdas_list = list(perdas)
    total_perdas = len(perdas_list)

    insight_perdas = None
    if total_perdas > 0:
        counter = Counter(perdas_list)
        etapa_top, count_top = counter.most_common(1)[0]
        percentual = round((count_top / total_perdas) * 100, 1)
        etapa_label = dict(EtapaOportunidade.choices).get(etapa_top, etapa_top)
        insight_perdas = {
            "etapa": etapa_label,
            "percentual": percentual,
            "total_perdas": total_perdas,
        }

    # 2. Cobertura pipeline vs meta
    hoje = timezone.now()
    qs_oport = Oportunidade.objects.exclude(
        etapa__in=[EtapaOportunidade.FECHAMENTO, EtapaOportunidade.PERDIDA]
    )
    if user is not None:
        qs_oport = aplicar_escopo_usuario(qs_oport, user, "vendedor")
    valor_pipeline = qs_oport.aggregate(
        total=Sum("valor_estimado")
    )["total"] or Decimal("0.00")

    qs_metas = MetaComercial.objects.filter(mes=hoje.month, ano=hoje.year)
    if user is not None:
        qs_metas = aplicar_escopo_usuario(qs_metas, user, "vendedor")
    soma_metas = qs_metas.aggregate(
        total=Sum("valor_meta")
    )["total"] or Decimal("0.00")

    insight_cobertura = None
    if soma_metas > 0:
        percentual_cobertura = round((valor_pipeline / soma_metas) * 100, 1)
        insight_cobertura = {
            "percentual": percentual_cobertura,
            "valor_pipeline": valor_pipeline,
            "soma_metas": soma_metas,
        }

    # 3. Dias médio parado (reutiliza qs_oport já filtrado)
    oportunidades_abertas = qs_oport

    insight_parada = None
    total_abertas = oportunidades_abertas.count()
    if total_abertas > 0:
        soma_dias = sum(
            (hoje - op.atualizado_em).total_seconds() / 86400
            for op in oportunidades_abertas
        )
        dias_medio = round(soma_dias / total_abertas, 1)
        insight_parada = {
            "dias_medio": dias_medio,
            "total_abertas": total_abertas,
        }

    return {
        "insight_perdas": insight_perdas,
        "insight_cobertura": insight_cobertura,
        "insight_parada": insight_parada,
    }
