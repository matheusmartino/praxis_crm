"""
Utilitário centralizado de escopo multi-tenant.

Garante que todas as queries respeitem:
  1. Empresa do usuário logado (via UsuarioEmpresa)
  2. Papel (ADMIN, GESTOR, VENDEDOR) (via Perfil)
  3. Hierarquia gestor → vendedor (via Perfil.gestor)
"""

from django.db.models import Q

from apps.core.enums import PerfilUsuario


def _obter_empresa(user):
    """Retorna a empresa do usuário ou None."""
    ue = getattr(user, "usuario_empresa", None)
    if ue is None:
        return None
    return ue.empresa


def aplicar_escopo_usuario(queryset, user, campo_usuario="vendedor"):
    """
    Filtra queryset conforme empresa e papel do usuário.

    Args:
        queryset: QuerySet a ser filtrado.
        user: Usuário logado (request.user).
        campo_usuario: Campo ForeignKey para User no model
                       (ex: "vendedor", "criado_por", "lead__criado_por").

    Regras:
        - Sempre filtra por empresa do usuário.
        - ADMIN: vê tudo da empresa.
        - GESTOR: vê dados dos seus vendedores + próprios.
        - VENDEDOR: vê apenas seus próprios dados.
        - Papel desconhecido ou sem perfil/empresa: queryset vazio.
    """
    perfil = getattr(user, "perfil", None)
    empresa = _obter_empresa(user)
    if not perfil or not empresa:
        return queryset.none()

    filtro_empresa = Q(**{f"{campo_usuario}__usuario_empresa__empresa": empresa})

    if perfil.papel == PerfilUsuario.ADMIN:
        return queryset.filter(filtro_empresa)

    if perfil.papel == PerfilUsuario.GESTOR:
        # Gestor vê dados dos seus vendedores + próprios dados
        filtro_vendedores = Q(**{f"{campo_usuario}__perfil__gestor": user})
        filtro_proprio = Q(**{campo_usuario: user})
        return queryset.filter(filtro_empresa & (filtro_vendedores | filtro_proprio))

    if perfil.papel == PerfilUsuario.VENDEDOR:
        return queryset.filter(filtro_empresa, **{campo_usuario: user})

    # Papel desconhecido
    return queryset.none()


def obter_usuarios_visiveis(user):
    """
    Retorna queryset de Users visíveis conforme papel do usuário.

    Usado em views de gestão que iteram sobre vendedores.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    perfil = getattr(user, "perfil", None)
    empresa = _obter_empresa(user)
    if not perfil or not empresa:
        return User.objects.none()

    base = User.objects.filter(usuario_empresa__empresa=empresa)

    if perfil.papel == PerfilUsuario.ADMIN:
        return base

    if perfil.papel == PerfilUsuario.GESTOR:
        return base.filter(Q(perfil__gestor=user) )

    if perfil.papel == PerfilUsuario.VENDEDOR:
        return base.filter(pk=user.pk)

    return User.objects.none()
