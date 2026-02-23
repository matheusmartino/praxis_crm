"""
Comando de seed para o modulo Carteira Ativa.

Uso:
    python manage.py seed_carteira_ativa

Comportamento:
  - Idempotente: pode ser executado N vezes sem duplicar registros.
  - NAO apaga dados existentes.
  - Reutiliza usuarios e clientes que ja existam pelo username/nome.

O que e criado:
  - Usuario vendedor1 (VENDEDOR) vinculado a empresa "Meta Mix"
  - Usuario gestor1   (GESTOR)   vinculado a mesma empresa
  - 15 clientes ATIVOS para o vendedor1, distribuidos em 4 grupos:
      Grupo A (3)  -> Sem contato (data_ultimo_contato = None)
      Grupo B (4)  -> Verde  (<= 20 dias)
      Grupo C (4)  -> Amarelo (21-40 dias)
      Grupo D (4)  -> Vermelho (41+ dias)
  - 1 ContatoCarteira por cliente dos Grupos B, C e D,
    com criado_em backdatado para corresponder a data_ultimo_contato.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Perfil
from apps.carteira_ativa.models import ContatoCarteira
from apps.core.enums import PerfilUsuario, StatusCliente, TipoCliente, TipoInteracao
from apps.core.models import Empresa, UsuarioEmpresa
from apps.crm.models import Cliente

User = get_user_model()

# -----------------------------------------------------------------------------
# Dados dos 15 clientes seed
#
# Campos:
#   nome         : identificador unico para get_or_create
#   tipo         : B2B ou B2C
#   cnpj_cpf     : obrigatorio pois status=ATIVO exige cnpj_cpf na validacao
#   telefone     : telefone ficticio para melhorar os dados de teste
#   delta_dias   : dias atras do ultimo contato (None = sem contato)
#   tipo_contato : TipoInteracao do ContatoCarteira (None se delta_dias=None)
# -----------------------------------------------------------------------------
CLIENTES_SEED = [
    # Grupo A -- Sem contato (3 clientes)
    {
        "nome": "Cliente Teste 01",
        "tipo": TipoCliente.B2B,
        "cnpj_cpf": "11.111.111/0001-01",
        "telefone": "(11) 91111-0001",
        "delta_dias": None,
        "tipo_contato": None,
    },
    {
        "nome": "Cliente Teste 02",
        "tipo": TipoCliente.B2C,
        "cnpj_cpf": "222.222.222-02",
        "telefone": "(11) 92222-0002",
        "delta_dias": None,
        "tipo_contato": None,
    },
    {
        "nome": "Cliente Teste 03",
        "tipo": TipoCliente.B2B,
        "cnpj_cpf": "33.333.333/0001-03",
        "telefone": "(11) 93333-0003",
        "delta_dias": None,
        "tipo_contato": None,
    },

    # Grupo B -- Verde (4 clientes, <= 20 dias)
    {
        "nome": "Cliente Teste 04",
        "tipo": TipoCliente.B2C,
        "cnpj_cpf": "444.444.444-04",
        "telefone": "(11) 94444-0004",
        "delta_dias": 5,
        "tipo_contato": TipoInteracao.LIGACAO,
    },
    {
        "nome": "Cliente Teste 05",
        "tipo": TipoCliente.B2B,
        "cnpj_cpf": "55.555.555/0001-05",
        "telefone": "(11) 95555-0005",
        "delta_dias": 10,
        "tipo_contato": TipoInteracao.EMAIL,
    },
    {
        "nome": "Cliente Teste 06",
        "tipo": TipoCliente.B2C,
        "cnpj_cpf": "666.666.666-06",
        "telefone": "(11) 96666-0006",
        "delta_dias": 15,
        "tipo_contato": TipoInteracao.WHATSAPP,
    },
    {
        "nome": "Cliente Teste 07",
        "tipo": TipoCliente.B2B,
        "cnpj_cpf": "77.777.777/0001-07",
        "telefone": "(11) 97777-0007",
        "delta_dias": 18,
        "tipo_contato": TipoInteracao.REUNIAO,
    },

    # Grupo C -- Amarelo (4 clientes, 21-40 dias)
    {
        "nome": "Cliente Teste 08",
        "tipo": TipoCliente.B2C,
        "cnpj_cpf": "888.888.888-08",
        "telefone": "(11) 98888-0008",
        "delta_dias": 22,
        "tipo_contato": TipoInteracao.LIGACAO,
    },
    {
        "nome": "Cliente Teste 09",
        "tipo": TipoCliente.B2B,
        "cnpj_cpf": "99.999.999/0001-09",
        "telefone": "(11) 99999-0009",
        "delta_dias": 28,
        "tipo_contato": TipoInteracao.VISITA,
    },
    {
        "nome": "Cliente Teste 10",
        "tipo": TipoCliente.B2C,
        "cnpj_cpf": "100.100.100-10",
        "telefone": "(11) 91000-0010",
        "delta_dias": 33,
        "tipo_contato": TipoInteracao.EMAIL,
    },
    {
        "nome": "Cliente Teste 11",
        "tipo": TipoCliente.B2B,
        "cnpj_cpf": "11.111.111/0002-11",
        "telefone": "(11) 91100-0011",
        "delta_dias": 38,
        "tipo_contato": TipoInteracao.WHATSAPP,
    },

    # Grupo D -- Vermelho (4 clientes, 41+ dias)
    {
        "nome": "Cliente Teste 12",
        "tipo": TipoCliente.B2C,
        "cnpj_cpf": "120.120.120-12",
        "telefone": "(11) 91200-0012",
        "delta_dias": 45,
        "tipo_contato": TipoInteracao.LIGACAO,
    },
    {
        "nome": "Cliente Teste 13",
        "tipo": TipoCliente.B2B,
        "cnpj_cpf": "13.131.313/0001-13",
        "telefone": "(11) 91300-0013",
        "delta_dias": 55,
        "tipo_contato": TipoInteracao.REUNIAO,
    },
    {
        "nome": "Cliente Teste 14",
        "tipo": TipoCliente.B2C,
        "cnpj_cpf": "140.140.140-14",
        "telefone": "(11) 91400-0014",
        "delta_dias": 60,
        "tipo_contato": TipoInteracao.EMAIL,
    },
    {
        "nome": "Cliente Teste 15",
        "tipo": TipoCliente.B2B,
        "cnpj_cpf": "15.151.515/0001-15",
        "telefone": "(11) 91500-0015",
        "delta_dias": 75,
        "tipo_contato": TipoInteracao.VISITA,
    },
]

# Observacao padrao por tipo de contato -- usada no ContatoCarteira
OBS_POR_TIPO = {
    TipoInteracao.LIGACAO:  "Ligacao realizada. Cliente confirmou interesse no produto.",
    TipoInteracao.EMAIL:    "E-mail enviado com proposta e condicoes comerciais.",
    TipoInteracao.WHATSAPP: "Contato via WhatsApp. Aguardando retorno do cliente.",
    TipoInteracao.REUNIAO:  "Reuniao de apresentacao realizada. Proximos passos alinhados.",
    TipoInteracao.VISITA:   "Visita presencial ao cliente. Demonstracao do produto.",
}


class Command(BaseCommand):
    help = "Seed de dados ficticios para o modulo Carteira Ativa (idempotente)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("[seed] Iniciando seed da Carteira Ativa..."))
        self.stdout.write("")

        # 1. Empresa (reusa "Meta Mix" do seed_crm ou cria como fallback)
        empresa = self._obter_ou_criar_empresa()

        # 2. Usuarios
        gestor1 = self._obter_ou_criar_usuario(
            username="gestor1",
            email="gestor1@crm.local",
            nome="Gestor",
            sobrenome="Carteira",
            papel=PerfilUsuario.GESTOR,
            empresa=empresa,
            gestor_user=None,
        )
        vendedor1 = self._obter_ou_criar_usuario(
            username="vendedor1",
            email="vendedor1@crm.local",
            nome="Vendedor",
            sobrenome="Carteira",
            papel=PerfilUsuario.VENDEDOR,
            empresa=empresa,
            gestor_user=gestor1,
        )

        self.stdout.write("")

        # 3 e 4. Clientes + ContatoCarteira
        self._seed_clientes(vendedor1)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("[OK] Seed finalizado com sucesso"))
        self.stdout.write(
            "     Acesse /carteira/ com vendedor1 (senha: 123456) para validar."
        )

    # -------------------------------------------------------------------------
    # Empresa
    # -------------------------------------------------------------------------

    def _obter_ou_criar_empresa(self) -> Empresa:
        """Reutiliza 'Meta Mix' (criada pelo seed_crm) ou cria como fallback."""
        empresa, created = Empresa.objects.get_or_create(
            nome="Meta Mix",
            defaults={"ativa": True},
        )
        if created:
            self.stdout.write(self.style.SUCCESS("  [+] Empresa criada: Meta Mix"))
        else:
            self.stdout.write(self.style.WARNING("  [=] Empresa reutilizada: Meta Mix"))
        return empresa

    # -------------------------------------------------------------------------
    # Usuarios
    # -------------------------------------------------------------------------

    def _obter_ou_criar_usuario(
        self, *, username, email, nome, sobrenome, papel, empresa, gestor_user
    ) -> User:
        """
        Cria ou reutiliza um usuario e garante Perfil + UsuarioEmpresa corretos.

        Usa Perfil.objects.filter(...).update() em vez de perfil.save() para
        definir papel e gestor -- evitando que o signal salvar_perfil sobrescreva
        os valores com a versao cacheada em memoria no objeto user.
        """
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": nome,
                "last_name": sobrenome,
                "is_active": True,
            },
        )

        # Garante que o Perfil existe no banco antes de user.save().
        Perfil.objects.get_or_create(user=user)

        if created:
            user.set_password("123456")
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"  [+] Usuario criado: {username} ({papel})")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"  [=] Usuario reutilizado: {username}")
            )

        # Usa update() direto no banco para evitar que o signal salvar_perfil
        # (accounts/signals.py) sobrescreva os valores com a versao cacheada
        # no objeto user (que ainda tem gestor=None no atributo em memoria).
        # update() nao dispara post_save, portanto o cache nao interfere.
        Perfil.objects.filter(user=user).update(papel=papel, gestor=gestor_user)

        # Garante vinculo com a empresa (cria ou atualiza)
        UsuarioEmpresa.objects.update_or_create(
            user=user,
            defaults={"empresa": empresa},
        )

        return user

    # -------------------------------------------------------------------------
    # Clientes + Contatos
    # -------------------------------------------------------------------------

    def _seed_clientes(self, vendedor: User) -> None:
        """
        Itera sobre CLIENTES_SEED e, para cada item:
          1. Obtem ou cria o Cliente (idempotente por nome).
          2. Atualiza data_ultimo_contato via queryset.update() para nao
             disparar auto_now em atualizado_em nem a validacao de clean().
          3. Cria 1 ContatoCarteira se ainda nao existir nenhum para o cliente,
             backdatando criado_em com queryset.update() (auto_now_add nao pode
             ser sobrescrito via save(), apenas via update() direto no banco).
        """
        agora = timezone.now()

        for dado in CLIENTES_SEED:
            nome = dado["nome"]
            delta = dado["delta_dias"]

            # -- Cria ou reutiliza o cliente ----------------------------------
            cliente, created = Cliente.objects.get_or_create(
                nome=nome,
                defaults={
                    "tipo": dado["tipo"],
                    "cnpj_cpf": dado["cnpj_cpf"],
                    "telefone": dado["telefone"],
                    "status": StatusCliente.ATIVO,
                    "criado_por": vendedor,
                    # data_ultimo_contato e definida abaixo via update()
                    "data_ultimo_contato": None,
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  [+] Cliente criado: {nome}"))
            else:
                self.stdout.write(self.style.WARNING(f"  [=] Cliente ja existe: {nome}"))

            # -- Define data_ultimo_contato (Grupos B, C, D) ------------------
            if delta is not None:
                data_contato = agora - timedelta(days=delta)
                # Usa update() direto para nao disparar auto_now em atualizado_em
                # e evitar re-executar clean().
                Cliente.objects.filter(pk=cliente.pk).update(
                    data_ultimo_contato=data_contato
                )
                # Atualiza o objeto em memoria para uso no ContatoCarteira abaixo
                cliente.data_ultimo_contato = data_contato
            # Grupo A: data_ultimo_contato permanece None

            # -- Cria ContatoCarteira (apenas se ainda nao houver nenhum) -----
            # Checa existencia antes de criar para garantir idempotencia.
            if delta is not None and not ContatoCarteira.objects.filter(
                cliente=cliente
            ).exists():
                tipo_contato = dado["tipo_contato"]
                obs = OBS_POR_TIPO.get(tipo_contato, "Contato registrado via seed.")

                # Cria com timestamp automatico (auto_now_add)
                contato = ContatoCarteira.objects.create(
                    cliente=cliente,
                    responsavel=vendedor,
                    tipo=tipo_contato,
                    observacao=obs,
                    proxima_acao_em=None,
                )

                # Backdating: ajusta criado_em para bater com data_ultimo_contato.
                # auto_now_add=True impede sobrescrever via save(), entao usamos
                # update() direto no banco -- tecnica padrao para fixtures/seeds.
                ContatoCarteira.objects.filter(pk=contato.pk).update(
                    criado_em=cliente.data_ultimo_contato
                )

                self.stdout.write(
                    f"       -> Contato: {nome} ({tipo_contato}, {delta}d atras)"
                )
