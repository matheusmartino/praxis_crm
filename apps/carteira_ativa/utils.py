"""
Módulo Carteira Ativa — utilitários de semáforo.

Centraliza a lógica de cor/prioridade para não duplicar entre views e services.
Importar daqui sempre que precisar calcular o semáforo ou os dias sem contato.
"""

from django.utils import timezone

# ─── Limiares (dias sem contato) ────────────────────────────────────────────
LIMIAR_VERDE = 20    # 0–20 dias → verde (em dia)
LIMIAR_AMARELO = 40  # 21–40 dias → amarelo (atenção)
#                      41+ dias → vermelho (crítico)
#                      None     → sem_contato (nunca houve contato)

# ─── Constantes de estado ────────────────────────────────────────────────────
SEMAFORO_VERDE = "verde"
SEMAFORO_AMARELO = "amarelo"
SEMAFORO_VERMELHO = "vermelho"
SEMAFORO_SEM_CONTATO = "sem_contato"

# ─── Config de apresentação por estado ──────────────────────────────────────
# Usado nos templates para evitar if/elif repetitivos.
SEMAFORO_CONFIG = {
    SEMAFORO_SEM_CONTATO: {
        "classe": "bg-secondary",
        "label": "Sem contato",
        "ordem": 0,  # prioridade máxima na ordenação manual
    },
    SEMAFORO_VERMELHO: {
        "classe": "bg-danger",
        "label": "Crítico",
        "ordem": 1,
    },
    SEMAFORO_AMARELO: {
        "classe": "bg-warning text-dark",
        "label": "Atenção",
        "ordem": 2,
    },
    SEMAFORO_VERDE: {
        "classe": "bg-success",
        "label": "Em dia",
        "ordem": 3,
    },
}


def limites_semaforo_dt() -> tuple:
    """
    Retorna (dt_verde, dt_amarelo) como datetimes timezone-aware para filtros de DB.

    Uso nas queries do banco:
      Verde   : data_ultimo_contato >= dt_verde
      Amarelo : dt_amarelo <= data_ultimo_contato < dt_verde
      Vermelho: data_ultimo_contato < dt_amarelo
      Sem cont: data_ultimo_contato IS NULL

    Centralizado aqui para que services.py nunca duplique os limiares.
    """
    from datetime import timedelta

    agora = timezone.now()
    return (
        agora - timedelta(days=LIMIAR_VERDE),    # dt_verde
        agora - timedelta(days=LIMIAR_AMARELO),  # dt_amarelo
    )


def calcular_semaforo(data_ultimo_contato) -> str:
    """
    Retorna o estado do semáforo com base na data do último contato.

    Regras:
      - None        → SEMAFORO_SEM_CONTATO  (nunca houve contato — prioridade máxima)
      - 0–20 dias   → SEMAFORO_VERDE
      - 21–40 dias  → SEMAFORO_AMARELO
      - 41+ dias    → SEMAFORO_VERMELHO

    Args:
        data_ultimo_contato: datetime aware, date, ou None.

    Returns:
        Uma das constantes SEMAFORO_* (str).
    """
    if data_ultimo_contato is None:
        return SEMAFORO_SEM_CONTATO

    hoje = timezone.now().date()

    # Suporta tanto DateTimeField (tem .date()) quanto DateField puro
    data = (
        data_ultimo_contato.date()
        if hasattr(data_ultimo_contato, "date")
        else data_ultimo_contato
    )

    dias = (hoje - data).days

    if dias <= LIMIAR_VERDE:
        return SEMAFORO_VERDE
    if dias <= LIMIAR_AMARELO:
        return SEMAFORO_AMARELO
    return SEMAFORO_VERMELHO


def dias_sem_contato(data_ultimo_contato) -> int | None:
    """
    Retorna quantos dias se passaram desde o último contato.
    Retorna None se nunca houve contato.
    """
    if data_ultimo_contato is None:
        return None

    hoje = timezone.now().date()
    data = (
        data_ultimo_contato.date()
        if hasattr(data_ultimo_contato, "date")
        else data_ultimo_contato
    )
    return (hoje - data).days
