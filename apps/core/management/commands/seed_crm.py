# apps/core/management/commands/seed_crm.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


from apps.accounts.models import Perfil
from apps.core.enums import PerfilUsuario
from apps.core.models import Empresa, UsuarioEmpresa

User = get_user_model()


class Command(BaseCommand):
    help = "Seed inicial do CRM: cria empresa, admin, gestor e vendedores"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Iniciando seed do CRM..."))

        # Empresa
        empresa = self.criar_empresa("Meta Mix")

        # Admin
        self.criar_usuario(
            username="admin",
            email="admin@crm.local",
            senha="123456",
            papel=PerfilUsuario.ADMIN,
            nome="Admin",
            sobrenome="Sistema",
            empresa=empresa,
            gestor=None,
            is_staff=True,
        )

        # Gestor
        gestor_user = self.criar_usuario(
            username="gestor",
            email="gestor@crm.local",
            senha="123456",
            papel=PerfilUsuario.GESTOR,
            nome="Carlos",
            sobrenome="Gestor",
            empresa=empresa,
            gestor=None,
        )

        # Vendedores vinculados ao gestor
        vendedores = [
            ("vendedor", "vendedor@crm.local", "Vendedor", "Padrao"),
            ("vendedor2", "vendedor2@crm.local", "Ana", "Vendedora"),
            ("vendedor3", "vendedor3@crm.local", "Bruno", "Vendas"),
        ]
        for username, email, nome, sobrenome in vendedores:
            self.criar_usuario(
                username=username,
                email=email,
                senha="123456",
                papel=PerfilUsuario.VENDEDOR,
                nome=nome,
                sobrenome=sobrenome,
                empresa=empresa,
                gestor=gestor_user,
            )

        self.stdout.write(self.style.SUCCESS("Seed finalizado com sucesso"))

    def criar_empresa(self, nome):
        empresa, created = Empresa.objects.get_or_create(
            nome=nome,
            defaults={"ativa": True},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  Empresa criada: {nome}"))
        else:
            self.stdout.write(self.style.WARNING(f"  Empresa ja existe: {nome}"))
        return empresa

    def criar_usuario(self, *, username, email, senha, papel, nome, sobrenome="",
                      empresa, gestor, is_staff=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": nome,
                "last_name": sobrenome,
                "is_active": True,
                "is_staff": is_staff,
            },
        )

        if created:
            user.set_password(senha)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"  Usuario {username} ({papel}) criado")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"  Usuario {username} ja existe — atualizando")
            )

        # Atualiza ou cria perfil (papel + gestor)
        perfil, _ = Perfil.objects.get_or_create(user=user)
        perfil.papel = papel
        perfil.gestor = gestor
        perfil.save()

        # Atualiza ou cria vinculo usuario-empresa
        UsuarioEmpresa.objects.update_or_create(
            user=user,
            defaults={"empresa": empresa},
        )

        return user
