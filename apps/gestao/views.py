from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.enums import EtapaOportunidade, StatusCliente
from apps.core.mixins import GestorRequiredMixin
from apps.core.utils.query_scope import aplicar_escopo_usuario, obter_usuarios_visiveis
from apps.crm.models import Cliente
from apps.prospeccao.models import Lead
from apps.sales.models import Oportunidade
from apps.sales.services import calcular_insights_gestao, calcular_tempo_medio_etapas

# Número de dias para considerar uma oportunidade como "parada"
DIAS_OPORTUNIDADE_PARADA = 7


class DashboardGestorView(GestorRequiredMixin, TemplateView):
    """Dashboard principal do gestor comercial."""

    template_name = "gestao/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Total de leads (clientes PROVISORIOS)
        context["total_leads"] = aplicar_escopo_usuario(
            Cliente.objects.filter(status=StatusCliente.PROVISORIO), user, "criado_por"
        ).count()

        # Total de clientes ativos
        context["total_clientes_ativos"] = aplicar_escopo_usuario(
            Cliente.objects.filter(status=StatusCliente.ATIVO), user, "criado_por"
        ).count()

        # Total de oportunidades (excluindo PERDIDA e FECHAMENTO)
        oportunidades_abertas = aplicar_escopo_usuario(
            Oportunidade.objects.exclude(
                etapa__in=[EtapaOportunidade.PERDIDA, EtapaOportunidade.FECHAMENTO]
            ),
            user,
            "vendedor",
        )
        context["total_oportunidades"] = oportunidades_abertas.count()

        # Valor total em pipeline
        context["valor_pipeline"] = (
            oportunidades_abertas.aggregate(total=Sum("valor_estimado"))["total"] or 0
        )

        # Oportunidades fechadas (ganhas)
        oportunidades_fechadas = aplicar_escopo_usuario(
            Oportunidade.objects.filter(etapa=EtapaOportunidade.FECHAMENTO),
            user,
            "vendedor",
        )
        context["total_fechadas"] = oportunidades_fechadas.count()

        # Valor total fechado
        context["valor_fechado"] = (
            oportunidades_fechadas.aggregate(total=Sum("valor_estimado"))["total"] or 0
        )

        # Alerta visual: oportunidades sem follow-up ou paradas
        data_limite = timezone.now() - timedelta(days=DIAS_OPORTUNIDADE_PARADA)

        sem_followup = oportunidades_abertas.filter(data_follow_up__isnull=True).count()
        paradas = oportunidades_abertas.filter(atualizado_em__lt=data_limite).count()

        context["oportunidades_sem_followup"] = sem_followup
        context["oportunidades_paradas"] = paradas
        context["dias_oportunidade_parada"] = DIAS_OPORTUNIDADE_PARADA
        context["total_alerta_disciplina"] = sem_followup + paradas

        # Insights e tempo médio por etapa
        context["tempo_medio_etapas"] = calcular_tempo_medio_etapas(user=user)
        context["insights"] = calcular_insights_gestao(user=user)

        return context


class LeadsPorVendedorView(GestorRequiredMixin, TemplateView):
    """Relatório de leads por vendedor."""

    template_name = "gestao/leads_por_vendedor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        vendedores_data = []
        vendedores = obter_usuarios_visiveis(user)

        for vendedor in vendedores:
            leads_criados = Lead.objects.filter(
                criado_por=vendedor
            ).count()

            total_clientes = Cliente.objects.filter(criado_por=vendedor).count()

            oportunidades_criadas = Oportunidade.objects.filter(
                vendedor=vendedor
            ).count()

            clientes_ids = Cliente.objects.filter(criado_por=vendedor).values_list(
                "id", flat=True
            )
            oportunidades_leads = Oportunidade.objects.filter(
                cliente_id__in=clientes_ids
            ).count()

            if total_clientes > 0:
                conversao = round((oportunidades_leads / total_clientes) * 100, 1)
            else:
                conversao = 0

            vendedores_data.append(
                {
                    "vendedor": vendedor,
                    "leads_criados": leads_criados,
                    "total_clientes": total_clientes,
                    "oportunidades_criadas": oportunidades_criadas,
                    "oportunidades_leads": oportunidades_leads,
                    "conversao": conversao,
                }
            )

        vendedores_data.sort(key=lambda x: x["leads_criados"], reverse=True)
        context["vendedores"] = vendedores_data

        return context


class PipelineGeralView(GestorRequiredMixin, TemplateView):
    """Visao geral do pipeline de vendas."""

    template_name = "gestao/pipeline_geral.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Pipeline por etapa
        etapas_data = []
        for etapa_code, etapa_label in EtapaOportunidade.choices:
            oportunidades = aplicar_escopo_usuario(
                Oportunidade.objects.filter(etapa=etapa_code), user, "vendedor"
            )
            quantidade = oportunidades.count()
            valor_total = oportunidades.aggregate(total=Sum("valor_estimado"))[
                "total"
            ] or 0

            etapas_data.append(
                {
                    "etapa": etapa_label,
                    "etapa_code": etapa_code,
                    "quantidade": quantidade,
                    "valor_total": valor_total,
                }
            )

        context["etapas"] = etapas_data

        # Pipeline por vendedor
        vendedores_pipeline = []
        vendedores = obter_usuarios_visiveis(user).filter(
            oportunidades__isnull=False
        ).distinct()

        for vendedor in vendedores:
            oportunidades_abertas = Oportunidade.objects.filter(
                vendedor=vendedor
            ).exclude(etapa__in=[EtapaOportunidade.PERDIDA, EtapaOportunidade.FECHAMENTO])

            quantidade = oportunidades_abertas.count()
            valor_total = oportunidades_abertas.aggregate(total=Sum("valor_estimado"))[
                "total"
            ] or 0

            etapas_vendedor = []
            for etapa_code, etapa_label in EtapaOportunidade.choices:
                if etapa_code in [EtapaOportunidade.PERDIDA, EtapaOportunidade.FECHAMENTO]:
                    continue
                ops_etapa = oportunidades_abertas.filter(etapa=etapa_code)
                qtd = ops_etapa.count()
                if qtd > 0:
                    etapas_vendedor.append(
                        {
                            "etapa": etapa_label,
                            "quantidade": qtd,
                            "valor": ops_etapa.aggregate(total=Sum("valor_estimado"))[
                                "total"
                            ]
                            or 0,
                        }
                    )

            vendedores_pipeline.append(
                {
                    "vendedor": vendedor,
                    "quantidade": quantidade,
                    "valor_total": valor_total,
                    "etapas": etapas_vendedor,
                }
            )

        vendedores_pipeline.sort(key=lambda x: x["valor_total"], reverse=True)
        context["vendedores_pipeline"] = vendedores_pipeline

        return context
