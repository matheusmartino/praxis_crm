# Praxis CRM

Sistema CRM para gestão de clientes, oportunidades e interações de vendas.

## Como rodar o projeto

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar migrações
python manage.py migrate

# Criar superusuário (admin)
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

Acesse `http://localhost:8000` no navegador.

## Fluxo do vendedor

1. Fazer login em `/accounts/login/`
2. No dashboard, ver oportunidades abertas e clientes recentes
3. Cadastrar clientes — status inicial é sempre **Provisório**
4. Criar oportunidades vinculadas a clientes
5. Registrar interações (ligação, e-mail, reunião, WhatsApp, visita)
6. Avançar etapas do pipeline: Prospecção → Qualificação → Proposta → Negociação → Fechamento
7. Marcar oportunidades como perdidas quando necessário

O vendedor só visualiza seus próprios clientes e oportunidades.

## Campos do cliente

| Campo | Descrição | Obrigatório |
|---|---|---|
| nome | Nome / Razão social | Sim |
| cnpj_cpf | CNPJ ou CPF | Opcional no cadastro rápido (provisório). **Obrigatório para ativar o cliente.** |
| tipo | B2B (PJ) ou B2C (PF) | Sim |
| telefone | Telefone da empresa | Não |
| email | E-mail da empresa | Não |
| nome_contato_principal | Nome do contato principal | Não |
| telefone_contato | Telefone do contato | Não |
| email_contato | E-mail do contato | Não |

### Regra de validação — CNPJ/CPF

O campo `cnpj_cpf` é opcional durante o cadastro rápido (cliente provisório). Ao tentar **ativar** o cliente (via Admin ou service), o sistema exige que o CNPJ/CPF esteja preenchido. Isso permite que o vendedor registre leads rapidamente sem burocracia e o admin só aprove clientes com documentação completa.

## Fluxo do admin

1. Acessar o Django Admin em `/admin/`
2. Ativar ou inativar clientes provisórios
3. Visualizar todos os clientes, oportunidades e interações
4. Gerenciar usuários e perfis

## Decisões de arquitetura

- **Settings split**: `config/settings/base.py` com configurações comuns, `dev.py` para desenvolvimento (SQLite), `prod.py` para produção (PostgreSQL via variáveis de ambiente)
- **Perfil como model separado**: `OneToOneField` para `User` com signal `post_save` para criação automática, evitando customizar `AbstractUser`
- **Services.py**: Regras de negócio isoladas em `services.py` por app. Views chamam services, services manipulam models
- **Enums centralizados**: Todos em `apps/core/enums.py` usando `models.TextChoices`
- **Filtro por vendedor**: Implementado nos querysets das views via mixin
- **Bootstrap 5 via CDN**: Sem necessidade de npm/webpack
