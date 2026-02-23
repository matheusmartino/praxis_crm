"""
Seed de dados para o módulo Prospecção.

Cria leads realistas em 8 cenários diferentes, utilizando o service
registrar_contato para garantir coerência entre contatos, follow-ups
e status dos leads.

Idempotente: leads com sufixo [SEED] não são recriados.

Uso:
    python manage.py seed_prospeccao
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.prospeccao.models import Lead, ResultadoContato, TipoContato
from apps.prospeccao.services import registrar_contato

SEED_TAG = "[SEED]"


def _lead_existe(nome):
    """Verifica se lead com esse nome já foi criado pelo seed."""
    return Lead.objects.filter(nome=nome).exists()


def _criar_lead(*, nome, empresa="", telefone, whatsapp="", email="",
                origem, produto_interesse="", observacoes=""):
    """Cria lead apenas se ainda não existir (idempotência)."""
    if _lead_existe(nome):
        return None
    return Lead.objects.create(
        nome=nome,
        empresa=empresa,
        telefone=telefone,
        whatsapp=whatsapp,
        email=email,
        origem=origem,
        produto_interesse=produto_interesse,
        observacoes=observacoes,
        criado_por_id=3
    )


class Command(BaseCommand):
    help = "Popula o módulo Prospecção com dados realistas para testes."

    def handle(self, *args, **options):
        hoje = timezone.now().date()
        contadores = {}

        with transaction.atomic():
            contadores["cenario_1"] = self._cenario_1_leads_novos()
            contadores["cenario_2"] = self._cenario_2_leads_em_contato()
            contadores["cenario_3"] = self._cenario_3_aguardando_retorno(hoje)
            contadores["cenario_4"] = self._cenario_4_followups_hoje(hoje)
            contadores["cenario_5"] = self._cenario_5_followups_atrasados(hoje)
            contadores["cenario_6"] = self._cenario_6_leads_perdidos()
            contadores["cenario_7"] = self._cenario_7_leads_convertidos()
            contadores["cenario_8"] = self._cenario_8_historico_intenso(hoje)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed de Prospecção executado com sucesso."))
        self.stdout.write("")
        self.stdout.write(f"  Cenário 1 — Leads Novos:            {contadores['cenario_1']} criados")
        self.stdout.write(f"  Cenário 2 — Em Contato:             {contadores['cenario_2']} criados")
        self.stdout.write(f"  Cenário 3 — Aguardando Retorno:     {contadores['cenario_3']} criados")
        self.stdout.write(f"  Cenário 4 — Follow-ups Hoje:        {contadores['cenario_4']} criados")
        self.stdout.write(f"  Cenário 5 — Follow-ups Atrasados:   {contadores['cenario_5']} criados")
        self.stdout.write(f"  Cenário 6 — Perdidos:               {contadores['cenario_6']} criados")
        self.stdout.write(f"  Cenário 7 — Convertidos:            {contadores['cenario_7']} criados")
        self.stdout.write(f"  Cenário 8 — Histórico Intenso:      {contadores['cenario_8']} criados")
        self.stdout.write("")
        total = sum(contadores.values())
        self.stdout.write(f"  Total: {total} leads criados nesta execução.")

    # ------------------------------------------------------------------
    # CENÁRIO 1 — Leads Novos (sem contato)
    # Status: NOVO | Contatos: 0 | FollowUp: 0
    # ------------------------------------------------------------------
    def _cenario_1_leads_novos(self):
        dados = [
            {"nome": f"João Silva {SEED_TAG}", "empresa": "Empresa Alfa Ltda",
             "telefone": "(11) 91234-0001", "origem": "Instagram",
             "produto_interesse": "Produto A"},
            {"nome": f"Maria Souza {SEED_TAG}", "empresa": "Souza & Cia",
             "telefone": "(11) 91234-0002", "origem": "Google",
             "produto_interesse": "Serviço Premium"},
            {"nome": f"Carlos Pereira {SEED_TAG}", "empresa": "",
             "telefone": "(21) 91234-0003", "origem": "Indicação",
             "produto_interesse": "Plano Anual"},
            {"nome": f"Fernanda Martins {SEED_TAG}", "empresa": "FM Consultoria",
             "telefone": "(31) 91234-0004", "origem": "Loja Física",
             "produto_interesse": "Consultoria"},
            {"nome": f"Rafael Oliveira {SEED_TAG}", "empresa": "",
             "telefone": "(41) 91234-0005", "origem": "Lista antiga",
             "produto_interesse": "Assinatura"},
        ]
        criados = 0
        for d in dados:
            lead = _criar_lead(**d)
            if lead:
                criados += 1
        return criados

    # ------------------------------------------------------------------
    # CENÁRIO 2 — Leads em contato
    # 1-2 contatos com NAO_ATENDEU ou INTERESSADO → status EM_CONTATO
    # ------------------------------------------------------------------
    def _cenario_2_leads_em_contato(self):
        dados = [
            {"nome": f"Ana Costa {SEED_TAG}", "empresa": "Costa Materiais",
             "telefone": "(11) 92345-0001", "origem": "Google",
             "produto_interesse": "Produto A",
             "contatos": [
                 (TipoContato.LIGACAO, ResultadoContato.NAO_ATENDEU, "Chamou e caiu na caixa postal."),
             ]},
            {"nome": f"Bruno Santos {SEED_TAG}", "empresa": "",
             "telefone": "(11) 92345-0002", "origem": "Instagram",
             "produto_interesse": "Serviço Premium",
             "contatos": [
                 (TipoContato.WHATSAPP, ResultadoContato.NAO_ATENDEU, "Mensagem enviada, sem resposta."),
                 (TipoContato.LIGACAO, ResultadoContato.INTERESSADO, "Atendeu, quer saber mais sobre preços."),
             ]},
            {"nome": f"Cláudia Lima {SEED_TAG}", "empresa": "Lima Engenharia",
             "telefone": "(21) 92345-0003", "origem": "Indicação",
             "produto_interesse": "Consultoria",
             "contatos": [
                 (TipoContato.PRESENCIAL, ResultadoContato.INTERESSADO, "Visitou a loja, ficou interessada."),
             ]},
            {"nome": f"Diego Rocha {SEED_TAG}", "empresa": "",
             "telefone": "(31) 92345-0004", "origem": "Loja Física",
             "produto_interesse": "Plano Anual",
             "contatos": [
                 (TipoContato.LIGACAO, ResultadoContato.NAO_ATENDEU, "Tentativa sem sucesso."),
                 (TipoContato.WHATSAPP, ResultadoContato.NAO_ATENDEU, "Enviou msg, não visualizou."),
             ]},
            {"nome": f"Elisa Mendes {SEED_TAG}", "empresa": "Mendes Saúde",
             "telefone": "(41) 92345-0005", "origem": "Google",
             "produto_interesse": "Assinatura",
             "contatos": [
                 (TipoContato.EMAIL, ResultadoContato.INTERESSADO, "Respondeu pedindo catálogo."),
             ]},
        ]
        criados = 0
        for d in dados:
            contatos = d.pop("contatos")
            lead = _criar_lead(**d)
            if lead:
                for tipo, resultado, obs in contatos:
                    registrar_contato(lead=lead, tipo=tipo, resultado=resultado, observacao=obs)
                criados += 1
        return criados

    # ------------------------------------------------------------------
    # CENÁRIO 3 — Leads aguardando retorno
    # Resultado PEDIU_RETORNO → status AGUARDANDO + FollowUp daqui 2 dias
    # ------------------------------------------------------------------
    def _cenario_3_aguardando_retorno(self, hoje):
        dados = [
            {"nome": f"Gabriel Nunes {SEED_TAG}", "empresa": "Nunes Tech",
             "telefone": "(11) 93456-0001", "origem": "Google",
             "produto_interesse": "Produto A"},
            {"nome": f"Helena Dias {SEED_TAG}", "empresa": "",
             "telefone": "(11) 93456-0002", "origem": "Instagram",
             "produto_interesse": "Serviço Premium"},
            {"nome": f"Igor Ferreira {SEED_TAG}", "empresa": "Ferreira & Filhos",
             "telefone": "(21) 93456-0003", "origem": "Indicação",
             "produto_interesse": "Consultoria"},
            {"nome": f"Juliana Alves {SEED_TAG}", "empresa": "",
             "telefone": "(31) 93456-0004", "origem": "Lista antiga",
             "produto_interesse": "Plano Anual"},
        ]
        criados = 0
        for d in dados:
            lead = _criar_lead(**d)
            if lead:
                registrar_contato(
                    lead=lead,
                    tipo=TipoContato.LIGACAO,
                    resultado=ResultadoContato.PEDIU_RETORNO,
                    observacao="Pediu para ligar daqui dois dias.",
                    proximo_contato=hoje + timedelta(days=2),
                )
                criados += 1
        return criados

    # ------------------------------------------------------------------
    # CENÁRIO 4 — Follow-ups HOJE
    # Resultado PEDIU_RETORNO → FollowUp com data = hoje
    # ------------------------------------------------------------------
    def _cenario_4_followups_hoje(self, hoje):
        dados = [
            {"nome": f"Karen Ribeiro {SEED_TAG}", "empresa": "Ribeiro Móveis",
             "telefone": "(11) 94567-0001", "origem": "Loja Física",
             "produto_interesse": "Produto A"},
            {"nome": f"Lucas Barbosa {SEED_TAG}", "empresa": "",
             "telefone": "(21) 94567-0002", "origem": "Google",
             "produto_interesse": "Assinatura"},
            {"nome": f"Mariana Teixeira {SEED_TAG}", "empresa": "Teixeira Eventos",
             "telefone": "(31) 94567-0003", "origem": "Indicação",
             "produto_interesse": "Serviço Premium"},
        ]
        criados = 0
        for d in dados:
            lead = _criar_lead(**d)
            if lead:
                registrar_contato(
                    lead=lead,
                    tipo=TipoContato.WHATSAPP,
                    resultado=ResultadoContato.PEDIU_RETORNO,
                    observacao="Pediu retorno para hoje.",
                    proximo_contato=hoje,
                )
                criados += 1
        return criados

    # ------------------------------------------------------------------
    # CENÁRIO 5 — Follow-ups ATRASADOS
    # FollowUp com data = hoje - 3 dias, ainda PENDENTE
    # ------------------------------------------------------------------
    def _cenario_5_followups_atrasados(self, hoje):
        dados = [
            {"nome": f"Nelson Cardoso {SEED_TAG}", "empresa": "",
             "telefone": "(11) 95678-0001", "origem": "Lista antiga",
             "produto_interesse": "Consultoria"},
            {"nome": f"Patrícia Gomes {SEED_TAG}", "empresa": "Gomes Alimentos",
             "telefone": "(21) 95678-0002", "origem": "Instagram",
             "produto_interesse": "Plano Anual"},
            {"nome": f"Roberto Lopes {SEED_TAG}", "empresa": "Lopes Auto Peças",
             "telefone": "(31) 95678-0003", "origem": "Google",
             "produto_interesse": "Produto A"},
        ]
        criados = 0
        for d in dados:
            lead = _criar_lead(**d)
            if lead:
                registrar_contato(
                    lead=lead,
                    tipo=TipoContato.LIGACAO,
                    resultado=ResultadoContato.PEDIU_RETORNO,
                    observacao="Pediu para retornar em breve.",
                    proximo_contato=hoje - timedelta(days=3),
                )
                criados += 1
        return criados

    # ------------------------------------------------------------------
    # CENÁRIO 6 — Leads Perdidos
    # Múltiplos contatos simulando tentativa, resultado final SEM_INTERESSE
    # → status PERDIDO
    # ------------------------------------------------------------------
    def _cenario_6_leads_perdidos(self):
        dados = [
            {"nome": f"Sandra Moreira {SEED_TAG}", "empresa": "",
             "telefone": "(11) 96789-0001", "origem": "Google",
             "produto_interesse": "Assinatura"},
            {"nome": f"Thiago Araújo {SEED_TAG}", "empresa": "Araújo Construções",
             "telefone": "(21) 96789-0002", "origem": "Indicação",
             "produto_interesse": "Produto A"},
            {"nome": f"Valéria Campos {SEED_TAG}", "empresa": "",
             "telefone": "(31) 96789-0003", "origem": "Loja Física",
             "produto_interesse": "Consultoria"},
            {"nome": f"Wesley Pinto {SEED_TAG}", "empresa": "Pinto Transportes",
             "telefone": "(41) 96789-0004", "origem": "Lista antiga",
             "produto_interesse": "Serviço Premium"},
        ]
        contatos_tentativa = [
            (TipoContato.LIGACAO, ResultadoContato.NAO_ATENDEU, "Primeira tentativa de contato."),
            (TipoContato.WHATSAPP, ResultadoContato.NAO_ATENDEU, "Mensagem enviada sem retorno."),
            (TipoContato.LIGACAO, ResultadoContato.SEM_INTERESSE, "Atendeu mas não tem interesse no momento."),
        ]
        criados = 0
        for d in dados:
            lead = _criar_lead(**d)
            if lead:
                for tipo, resultado, obs in contatos_tentativa:
                    registrar_contato(lead=lead, tipo=tipo, resultado=resultado, observacao=obs)
                criados += 1
        return criados

    # ------------------------------------------------------------------
    # CENÁRIO 7 — Leads Convertidos
    # Pelo menos 2 contatos antes do fechamento → status CONVERTIDO
    # convertido_em preenchido automaticamente pelo service
    # ------------------------------------------------------------------
    def _cenario_7_leads_convertidos(self):
        dados = [
            {"nome": f"Amanda Vieira {SEED_TAG}", "empresa": "Vieira Soluções",
             "telefone": "(11) 97890-0001", "origem": "Indicação",
             "produto_interesse": "Plano Anual"},
            {"nome": f"Bernardo Cunha {SEED_TAG}", "empresa": "",
             "telefone": "(21) 97890-0002", "origem": "Google",
             "produto_interesse": "Serviço Premium"},
            {"nome": f"Camila Duarte {SEED_TAG}", "empresa": "Duarte Arquitetura",
             "telefone": "(31) 97890-0003", "origem": "Instagram",
             "produto_interesse": "Consultoria"},
        ]
        contatos_jornada = [
            (TipoContato.LIGACAO, ResultadoContato.INTERESSADO, "Primeiro contato, demonstrou interesse."),
            (TipoContato.PRESENCIAL, ResultadoContato.INTERESSADO, "Reunião presencial, gostou da proposta."),
            (TipoContato.WHATSAPP, ResultadoContato.FECHOU, "Confirmou fechamento por WhatsApp."),
        ]
        criados = 0
        for d in dados:
            lead = _criar_lead(**d)
            if lead:
                for tipo, resultado, obs in contatos_jornada:
                    registrar_contato(lead=lead, tipo=tipo, resultado=resultado, observacao=obs)
                criados += 1
        return criados

    # ------------------------------------------------------------------
    # CENÁRIO 8 — Lead com histórico intenso
    # 5 contatos alternando resultados, último INTERESSADO + FollowUp hoje
    # ------------------------------------------------------------------
    def _cenario_8_historico_intenso(self, hoje):
        nome = f"Daniel Monteiro {SEED_TAG}"
        lead = _criar_lead(
            nome=nome,
            empresa="Monteiro & Associados",
            telefone="(11) 98901-0001",
            whatsapp="(11) 98901-0001",
            email="daniel.monteiro@example.com",
            origem="Indicação",
            produto_interesse="Produto A",
            observacoes="Lead prioritário, indicado por cliente VIP.",
        )
        if not lead:
            return 0

        contatos = [
            (TipoContato.LIGACAO, ResultadoContato.NAO_ATENDEU,
             "Primeira tentativa, não atendeu."),
            (TipoContato.WHATSAPP, ResultadoContato.PEDIU_RETORNO,
             "Respondeu pedindo para ligar na semana seguinte."),
            (TipoContato.LIGACAO, ResultadoContato.INTERESSADO,
             "Atendeu, quer receber proposta comercial."),
            (TipoContato.EMAIL, ResultadoContato.NAO_ATENDEU,
             "Enviou proposta por e-mail, sem resposta ainda."),
            (TipoContato.LIGACAO, ResultadoContato.INTERESSADO,
             "Confirmou recebimento da proposta, vai analisar."),
        ]

        # Registra os 4 primeiros contatos sem follow-up
        for tipo, resultado, obs in contatos[:-1]:
            registrar_contato(lead=lead, tipo=tipo, resultado=resultado, observacao=obs)

        # Último contato com follow-up para hoje
        tipo, resultado, obs = contatos[-1]
        registrar_contato(
            lead=lead,
            tipo=tipo,
            resultado=resultado,
            observacao=obs,
            proximo_contato=hoje,
        )
        return 1
