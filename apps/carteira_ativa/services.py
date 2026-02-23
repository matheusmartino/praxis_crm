"""
Módulo Carteira Ativa — services.

Toda a regra de negócio fica aqui. As views chamam estas funções
e não fazem queries diretamente, mantendo o código testável e limpo.

Funções disponíveis:
  listar_carteira()     → QuerySet de clientes ATIVOS e PROVISORIOS (sem ordenação especial)
  listar_fila()         → igual, mas com ordenação de semáforo e filtro por estado
  obter_cliente_ativo() → busca segura com escopo do usuário
  registrar_contato()   → cria ContatoCarteira e atualiza data_ultimo_contato
"""

import logging
from datetime import timedelta

from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from apps.core.enums import StatusCliente
from apps.core.utils.query_scope import aplicar_escopo_usuario
from apps.crm.models import Cliente

logger = logging.getLogger("praxis.carteira_ativa")


# ─── Helpers de escopo ───────────────────────────────────────────────────────

def listar_carteira(user, *, nome: str = "", tipo: str = ""):
    """
    QuerySet base: clientes ATIVO e PROVISORIO no escopo do usuário.

    Aplica:
      - status__in=[ATIVO, PROVISORIO]
      - escopo multi-tenant (vendedor vê só os seus; gestor/admin vê todos da empresa)
      - filtros opcionais de nome e tipo

    Usado internamente por listar_fila(), obter_cliente_ativo() e
    obter_metricas_dashboard().

    # Carteira Ativa considera clientes ATIVO e PROVISORIO
    # pois a empresa ainda não utiliza plenamente o fluxo de status do CRM.
    # Isso evita que novos clientes fiquem fora da carteira operacional.
    """
    # Carteira Ativa considera clientes ATIVO e PROVISORIO
    # pois a empresa ainda não utiliza plenamente o fluxo de status do CRM.
    # Isso evita que novos clientes fiquem fora da carteira operacional.
    qs = Cliente.objects.filter(
        status__in=[StatusCliente.ATIVO, StatusCliente.PROVISORIO]
    )
    qs = aplicar_escopo_usuario(qs, user, "criado_por")

    if nome:
        qs = qs.filter(nome__icontains=nome)
    if tipo:
        qs = qs.filter(tipo=tipo)

    return qs


def listar_fila(user, *, nome: str = "", tipo: str = "", semaforo: str = ""):
    """
    QuerySet da fila de contato, pronto para a view FilaView.

    Ordenação:
      1. Clientes sem contato (data_ultimo_contato IS NULL) — topo
      2. Clientes com contato mais antigo primeiro (vermelho → amarelo → verde)

    Filtro por semáforo (param `semaforo`):
      "sem_contato" → data_ultimo_contato IS NULL
      "verde"       → último contato nos últimos 20 dias
      "amarelo"     → último contato entre 21 e 40 dias atrás
      "vermelho"    → último contato há mais de 40 dias

    A lógica de limiares é definida em utils.py (LIMIAR_VERDE, LIMIAR_AMARELO)
    e replicada aqui para filtros de DB — mantidas em sincronia manualmente.
    """
    qs = listar_carteira(user, nome=nome, tipo=tipo)

    # ── Filtro por semáforo ──────────────────────────────────────────────────
    if semaforo:
        agora = timezone.now()
        if semaforo == "sem_contato":
            qs = qs.filter(data_ultimo_contato__isnull=True)
        elif semaforo == "verde":
            # Até 20 dias atrás
            limite = agora - timedelta(days=20)
            qs = qs.filter(data_ultimo_contato__gte=limite)
        elif semaforo == "amarelo":
            # Entre 21 e 40 dias atrás
            limite_recente = agora - timedelta(days=21)
            limite_antigo = agora - timedelta(days=40)
            qs = qs.filter(
                data_ultimo_contato__lte=limite_recente,
                data_ultimo_contato__gte=limite_antigo,
            )
        elif semaforo == "vermelho":
            # Mais de 40 dias atrás
            limite = agora - timedelta(days=41)
            qs = qs.filter(data_ultimo_contato__lte=limite)

    # ── Ordenação: sem contato primeiro, depois mais antigo ──────────────────
    # sem_contato_sort=0 → NULL (nunca contatado) vai para o topo
    # sem_contato_sort=1 → tem data, ordena por data_ultimo_contato ASC
    qs = qs.annotate(
        sem_contato_sort=Case(
            When(data_ultimo_contato__isnull=True, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by("sem_contato_sort", "data_ultimo_contato")

    return qs


def obter_cliente_ativo(pk: int, user) -> Cliente:
    """
    Retorna um cliente ATIVO pelo pk, respeitando o escopo do usuário.

    Lança Http404 se não encontrado ou fora do escopo.
    Não lança PermissionDenied — o 404 é intencional para não vazar informação.
    """
    from django.http import Http404

    try:
        return listar_carteira(user).get(pk=pk)
    except Cliente.DoesNotExist:
        raise Http404("Cliente ativo não encontrado.")


# ─── Motor de contato (Etapa 2) ──────────────────────────────────────────────

def registrar_contato(
    *,
    cliente: Cliente,
    usuario,
    tipo: str,
    observacao: str = "",
    proxima_acao_em=None,
):
    """
    Registra um contato com um cliente ativo e mantém data_ultimo_contato atualizado.

    Comportamento:
      1. Valida que o cliente está ATIVO (salvaguarda — a view já garante isso via escopo).
      2. Cria ContatoCarteira com os dados fornecidos.
      3. Atualiza cliente.data_ultimo_contato com o timestamp do contato recém-criado.
         Usa update_fields para não sobrescrever outros campos e evitar race conditions.
      4. Loga e retorna o objeto ContatoCarteira criado.

    Args:
        cliente: instância de Cliente (deve estar ATIVO)
        usuario: request.user — responsável pelo contato
        tipo: str — valor de TipoInteracao (ex: "LIGACAO")
        observacao: str — notas livres (default: "")
        proxima_acao_em: date | None — sugestão de próximo contato

    Returns:
        ContatoCarteira recém-criado.

    Raises:
        ValueError: se o cliente não estiver com status ATIVO.
    """
    from apps.carteira_ativa.models import ContatoCarteira

    # Salvaguarda explícita: nunca registrar contato em cliente não-ativo
    if cliente.status != StatusCliente.ATIVO:
        raise ValueError(
            f"Não é possível registrar contato: cliente '{cliente}' "
            f"não está ATIVO (status atual: {cliente.status})."
        )

    # Cria o registro de contato
    contato = ContatoCarteira.objects.create(
        cliente=cliente,
        responsavel=usuario,
        tipo=tipo,
        observacao=observacao,
        proxima_acao_em=proxima_acao_em,
    )

    # Atualiza apenas data_ultimo_contato no cliente.
    # criado_em do contato é timezone-aware (auto_now_add com USE_TZ=True).
    # update_fields garante que não sobrescrevemos campos que podem ter sido
    # alterados por outro processo concorrente.
    cliente.data_ultimo_contato = contato.criado_em
    cliente.save(update_fields=["data_ultimo_contato"])

    logger.info(
        "Contato registrado | cliente_id=%s cliente='%s' tipo=%s responsavel=%s",
        cliente.pk,
        cliente.nome,
        tipo,
        usuario.get_username(),
    )

    return contato


# ─── Dashboard do Gestor ──────────────────────────────────────────────────────

def obter_metricas_dashboard(user) -> dict:
    """
    Calcula todas as métricas do Dashboard do Gestor em poucas queries de DB.

    Estratégia: COUNT + filtros condicionais (Q objects) — sem loops Python.

    Args:
        user: GESTOR ou ADMIN autenticado. O escopo (empresa + hierarquia)
              é aplicado automaticamente por listar_carteira().

    Retorna um dict com:
      kpis         – totais globais de semáforo (total, sem_contato, verde,
                     amarelo, vermelho)
      por_vendedor – lista de dicts; um item por criado_por com subtotais
      contatos_30d – lista de dicts; contatos nos últimos 30 dias por responsável
      tocados_7d   – int: clientes que receberam contato nos últimos 7 dias
    """
    from datetime import timedelta

    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q

    from apps.carteira_ativa.models import ContatoCarteira
    from apps.carteira_ativa.utils import limites_semaforo_dt

    User = get_user_model()
    agora = timezone.now()

    # Limiares calculados uma única vez e reutilizados em todos os filtros
    dt_verde, dt_amarelo = limites_semaforo_dt()
    dt_30d = agora - timedelta(days=30)
    dt_7d = agora - timedelta(days=7)

    # Base escoped: clientes ATIVOS visíveis para o usuário (empresa + papel)
    base_qs = listar_carteira(user)

    # Reutilizamos os mesmos Q objects em aggregate() e em annotate()
    # para garantir que as contagens são idênticas entre KPIs e por_vendedor.
    q_sem = Q(data_ultimo_contato__isnull=True)
    q_verde = Q(data_ultimo_contato__gte=dt_verde)
    q_amarelo = Q(
        data_ultimo_contato__lt=dt_verde,
        data_ultimo_contato__gte=dt_amarelo,
    )
    q_vermelho = Q(data_ultimo_contato__lt=dt_amarelo)

    # ── KPIs globais: uma única query com COUNT condicional ───────────────────
    kpis = base_qs.aggregate(
        total=Count("id"),
        sem_contato=Count("id", filter=q_sem),
        verde=Count("id", filter=q_verde),
        amarelo=Count("id", filter=q_amarelo),
        vermelho=Count("id", filter=q_vermelho),
    )

    # ── Distribuição por vendedor: GROUP BY criado_por_id ────────────────────
    # .order_by("-total") substitui o ordering padrão do Meta (-criado_em)
    # para evitar que o ORDER BY vaze para dentro do GROUP BY.
    por_vendedor_raw = list(
        base_qs
        .values("criado_por_id")
        .annotate(
            total=Count("id"),
            sem_contato=Count("id", filter=q_sem),
            verde=Count("id", filter=q_verde),
            amarelo=Count("id", filter=q_amarelo),
            vermelho=Count("id", filter=q_vermelho),
        )
        .order_by("-total")
    )

    # Busca nomes de todos os vendedores em uma única query com __in (evita N+1)
    user_ids = [r["criado_por_id"] for r in por_vendedor_raw]
    users_map = User.objects.filter(pk__in=user_ids).in_bulk()

    por_vendedor = []
    for row in por_vendedor_raw:
        u = users_map.get(row["criado_por_id"])
        por_vendedor.append({
            **row,
            "nome_vendedor": u.get_full_name() or u.username if u else "—",
        })

    # ── Contatos últimos 30 dias: GROUP BY responsavel_id ────────────────────
    # cliente__in usa base_qs como subquery, garantindo o mesmo escopo.
    # .order_by() em base_qs remove o ORDER BY interno da subquery (inválido
    # em alguns backends SQL quando usado dentro de IN).
    contatos_30d_raw = list(
        ContatoCarteira.objects
        .filter(criado_em__gte=dt_30d, cliente__in=base_qs.order_by())
        .values("responsavel_id")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    resp_ids = [r["responsavel_id"] for r in contatos_30d_raw]
    resp_map = User.objects.filter(pk__in=resp_ids).in_bulk()

    contatos_30d = []
    for row in contatos_30d_raw:
        u = resp_map.get(row["responsavel_id"])
        contatos_30d.append({
            **row,
            "nome_vendedor": u.get_full_name() or u.username if u else "—",
        })

    # ── KPI extra: clientes com contato nos últimos 7 dias ───────────────────
    tocados_7d = base_qs.filter(data_ultimo_contato__gte=dt_7d).count()

    return {
        "kpis": kpis,
        "por_vendedor": por_vendedor,
        "contatos_30d": contatos_30d,
        "tocados_7d": tocados_7d,
    }
