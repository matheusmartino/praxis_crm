from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal


from apps.core.enums import EtapaOportunidade
from apps.crm.models import Cliente
from apps.sales.models import Oportunidade


User = get_user_model()


class Command(BaseCommand):
    help = "Seed inicial do CRM: usuários, clientes e oportunidades"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🌱 Iniciando seed do CRM..."))

        vendedor = User.objects.get(username="vendedor")

        clientes = self.seed_clientes()
        self.seed_oportunidades(clientes, vendedor)

        self.stdout.write(self.style.SUCCESS("✅ Seed finalizado com sucesso"))

    # -------------------------
    # Clientes
    # -------------------------
    def seed_clientes(self):
        dados = [
            {
                "nome": "Alpha Indústria LTDA",
                "email": "contato@alpha.com",
                "telefone": "(11) 99999-1111",
            },
            {
                "nome": "Beta Comércio ME",
                "email": "financeiro@beta.com",
                "telefone": "(16) 98888-2222",
            },
            {
                "nome": "Gamma Serviços",
                "email": "admin@gamma.com",
                "telefone": "(21) 97777-3333",
            },
        ]

        clientes = []

        for item in dados:
            cliente, created = Cliente.objects.get_or_create(
                nome=item["nome"],
                defaults={
                    "email": item["email"],
                    "telefone": item["telefone"],
                    #"ativo": True,
                    "criado_por": User.objects.get(username="admin"),
                },
            )

            if created:
                self.stdout.write(f"✔ Cliente criado: {cliente.nome}")
            else:
                self.stdout.write(f"⚠ Cliente já existe: {cliente.nome}")

            clientes.append(cliente)

        return clientes

    # -------------------------
    # Oportunidades
    # -------------------------
    def seed_oportunidades(self, clientes, vendedor):
        dados = [
            {
                "titulo": "Venda de licenças CRM",
                "valor_estimado": Decimal("3500.00"),
                "etapa": EtapaOportunidade.NEGOCIACAO,
            },
            {
                "titulo": "Implantação e treinamento",
                "valor_estimado": Decimal("5200.00"),
                "etapa": EtapaOportunidade.PROPOSTA,
            },
            {
                "titulo": "Contrato anual",
                "valor_estimado": Decimal("18000.00"),
                "etapa": EtapaOportunidade.PROSPECCAO,
            },
        ]

        for cliente in clientes:
            for item in dados:
                oportunidade, created = Oportunidade.objects.get_or_create(
                    cliente=cliente,
                    titulo=item["titulo"],
                    defaults={
                        "valor_estimado": item["valor_estimado"],
                        "etapa": item["etapa"],
                        "vendedor": vendedor,
                    },
                )

                if created:
                    self.stdout.write(
                        f"✔ Oportunidade criada: {cliente.nome} → {item['titulo']}"
                    )
                else:
                    self.stdout.write(
                        f"⚠ Oportunidade já existe: {cliente.nome} → {item['titulo']}"
                    )
