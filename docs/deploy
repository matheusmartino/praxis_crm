# 🚀 Deploy Oficial — Projeto Django

Este documento descreve a estratégia oficial de deploy do projeto utilizando:

- Azure DevOps (CI/CD)
- VPS Linux (Ubuntu)
- Gunicorn
- Nginx
- PostgreSQL
- Separação de ambientes DEV e PRD

---

# 🏗️ Arquitetura Geral

```
Internet
   ↓
Nginx
   ↓
┌─────────────┬─────────────┐
│ PRD         │ DEV         │
│ Gunicorn    │ Gunicorn    │
│ Porta 8000  │ Porta 8001  │
└─────────────┴─────────────┘
```

---

# 🌳 Estratégia de Branch

```
main      → Produção
develop   → Desenvolvimento / QA
feature/* → Desenvolvimento isolado
```

## Fluxo Oficial

1. Desenvolver em `feature/*`
2. Merge para `develop`
3. Deploy automático em DEV
4. Testes e validação
5. Merge para `main`
6. Deploy automático em PRD

---

# 📂 Estrutura no VPS

```
/home/app/
   ├── dev/
   │     ├── app/
   │     ├── venv/
   │     ├── .env
   │     ├── logs/
   │
   └── prod/
         ├── app/
         ├── venv/
         ├── .env
         ├── logs/
```

Cada ambiente é isolado.

---

# ⚙️ Configuração do Django

## Estrutura de settings

```
config/settings/
   base.py
   dev.py
   prod.py
```

### base.py
Contém configurações comuns.

### dev.py
- DEBUG = True
- Banco DEV
- ALLOWED_HOSTS para ambiente de teste

### prod.py
- DEBUG = False
- Banco PRD
- ALLOWED_HOSTS configurado
- Segurança ativada

---

# 🔐 Variáveis de Ambiente (.env)

Cada ambiente possui seu próprio `.env`.

## Exemplo PRD

```
SECRET_KEY=chave_super_secreta
DB_NAME=db_prod
DB_USER=user_prod
DB_PASSWORD=senha_prod
DB_HOST=localhost
```

Nunca versionar `.env`.

Adicionar ao `.gitignore`:

```
.env
```

---

# 🧠 Banco de Dados

Mesmo PostgreSQL, bancos separados:

```
db_dev
db_prod
```

Nunca compartilhar banco entre ambientes.

---

# 🔧 Gunicorn

## PRD

Arquivo:
```
/etc/systemd/system/gunicorn-prod.service
```

```
[Unit]
Description=Gunicorn PRD
After=network.target

[Service]
User=app
Group=www-data
WorkingDirectory=/home/app/prod/app
Environment="DJANGO_SETTINGS_MODULE=config.settings.prod"
ExecStart=/home/app/prod/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

---

## DEV

Arquivo:
```
/etc/systemd/system/gunicorn-dev.service
```

```
[Unit]
Description=Gunicorn DEV
After=network.target

[Service]
User=app
Group=www-data
WorkingDirectory=/home/app/dev/app
Environment="DJANGO_SETTINGS_MODULE=config.settings.dev"
ExecStart=/home/app/dev/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8001

[Install]
WantedBy=multi-user.target
```

Ativar serviços:

```
sudo systemctl daemon-reload
sudo systemctl enable gunicorn-prod
sudo systemctl enable gunicorn-dev
sudo systemctl start gunicorn-prod
sudo systemctl start gunicorn-dev
```

---

# 🌐 Nginx

## PRD

Arquivo:
```
/etc/nginx/sites-available/prod
```

```
server {
    server_name sistema.com;

    location /static/ {
        alias /home/app/prod/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        include proxy_params;
    }
}
```

---

## DEV

Arquivo:
```
/etc/nginx/sites-available/dev
```

```
server {
    server_name dev.sistema.com;

    location /static/ {
        alias /home/app/dev/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        include proxy_params;
    }
}
```

Ativar:

```
sudo ln -s /etc/nginx/sites-available/prod /etc/nginx/sites-enabled
sudo ln -s /etc/nginx/sites-available/dev /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

# 🔁 Processo Manual de Deploy

## DEV

```
cd /home/app/dev/app
git pull origin develop
source ../venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn-dev
```

---

## PRD

```
cd /home/app/prod/app
git pull origin main
source ../venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn-prod
```

---

# 🔵 Azure DevOps (CI/CD)

Pipeline com 3 stages:

- Build
- Deploy_DEV (branch develop)
- Deploy_PRD (branch main)

O pipeline deve:

1. Rodar testes automatizados
2. Fazer SSH na VPS
3. Executar comandos de deploy
4. Reiniciar serviço automaticamente

---

# 🛡️ Segurança

Checklist obrigatório:

- SSH via chave (sem senha)
- Firewall liberando apenas 80 e 443
- Banco não exposto externamente
- Backup diário automático
- DEBUG=False em PRD
- HTTPS configurado
- .env nunca versionado

---

# 🔐 Certificado SSL

Instalar Certbot:

```
sudo certbot --nginx -d sistema.com
sudo certbot --nginx -d dev.sistema.com
```

Renovação automática:

```
sudo certbot renew --dry-run
```

---

# 📊 Fluxo Oficial do Projeto

```
Feature → Develop → Deploy DEV
                 ↓
               Testes
                 ↓
               Main → Deploy PRD
```

---

# 🧱 Regras do Projeto

- Nunca commitar `.env`
- Nunca usar DEBUG=True em PRD
- Nunca compartilhar banco entre ambientes
- Nunca usar `runserver` na VPS
- Sempre rodar migrate antes de restart
- Sempre validar `nginx -t` antes de reiniciar

---

# 🚀 Evoluções Futuras

- Dockerização
- Blue/Green Deploy
- Monitoramento (Sentry)
- Health Check automático
- Backup automatizado com retenção
- Versionamento formal de release

---

# 📌 Status

Estratégia preparada para:

- Escalar
- Separar ambientes corretamente
- Automatizar CI/CD
- Crescimento seguro e organizado
