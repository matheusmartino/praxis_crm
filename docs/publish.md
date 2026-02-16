# 🚀 Praxis CRM — Guia Oficial de Deploy (Produção)

Infraestrutura validada e estabilizada após múltiplos ajustes reais em VPS Hostinger.

Servidor:
- Ubuntu
- Usuário Linux: `app`
- Diretório do projeto: `/home/app/prod`
- App Django em: `/home/app/prod/app`
- Virtualenv em: `/home/app/prod/venv`
- Gunicorn + Nginx + PostgreSQL
- GitHub Actions com Self-Hosted Runner

---

# 🧱 Estrutura Final do Servidor

```
/home/app/prod
├── app/
│   ├── manage.py
│   ├── config/
│   ├── apps/
│   ├── static/
│   ├── staticfiles/
│   └── templates/
├── venv/
├── logs/
└── .env
```

---

# 🐘 Banco de Dados (PostgreSQL)

Usuário:
```
usuario_prod
```

Configuração no `prod.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "praxis_db",
        "USER": "usuario_prod",
        "PASSWORD": "SENHA_AQUI",
        "HOST": "127.0.0.1",
        "PORT": "5432",
        "CONN_MAX_AGE": 60,
    }
}
```

---

# ⚙️ config/wsgi.py (CRÍTICO)

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
```

Nunca deixar apontando para `dev`.

---

# 🔧 Service systemd

Arquivo:

```
/etc/systemd/system/praxis.service
```

Conteúdo:

```
[Unit]
Description=Gunicorn daemon for Praxis
After=network.target

[Service]
User=app
Group=www-data
WorkingDirectory=/home/app/prod/app
ExecStart=/home/app/prod/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/home/app/prod/app/praxis.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Depois:

```
sudo systemctl daemon-reload
sudo systemctl enable praxis
sudo systemctl restart praxis
```

---

# 🌐 Nginx

Arquivo:

```
/etc/nginx/sites-available/praxis
```

Configuração:

```
server {
    listen 80;
    server_name praxisapp.com.br www.praxisapp.com.br;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /home/app/prod/app;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/app/prod/app/praxis.sock;
    }
}
```

---

# 🌍 DNS (Hostinger)

Registros:

```
A      @      187.77.37.217
CNAME  www    praxisapp.com.br
```

Remover qualquer A duplicado.

---

# 🔐 ALLOWED_HOSTS (prod.py)

```python
ALLOWED_HOSTS = [
    "praxisapp.com.br",
    ".praxisapp.com.br",
    "187.77.37.217",
]
```

---

# 🚀 Deploy Automatizado — GitHub Actions (Self-Hosted Runner)

## Por que Self-Hosted?

Abrir porta 22 para GitHub runners públicos é inseguro.
Os IPs mudam constantemente.

Solução segura:
- Runner instalado dentro do VPS
- Runner "puxa" os jobs
- Não é necessário abrir SSH externo

---

## 📦 Instalação do Runner (usuário app)

```
mkdir ~/actions-runner
cd ~/actions-runner
```

Baixar corretamente:

```
curl -o actions-runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.317.0/actions-runner-linux-x64-2.317.0.tar.gz
tar xzf actions-runner.tar.gz
```

Configurar:

```
./config.sh
```

Instalar como serviço:

```
sudo ./svc.sh install
sudo ./svc.sh start
```

---

## 🔐 Permissão sudo controlada

Para permitir restart do serviço sem dar sudo total:

```
sudo visudo
```

Adicionar:

```
app ALL=(ALL) NOPASSWD: /bin/systemctl restart praxis
```

Isso permite apenas:

```
sudo systemctl restart praxis
```

Nada mais.

---

## 📄 Workflow GitHub

`.github/workflows/deploy.yml`

```
name: Deploy

on:
  push:
    branches:
      - master

jobs:
  deploy:
    runs-on: self-hosted

    steps:
      - name: Pull code
        run: |
          cd /home/app/prod/app
          git pull origin master

      - name: Install dependencies
        run: |
          cd /home/app/prod
          source venv/bin/activate
          pip install -r app/requirements.txt

      - name: Migrate
        run: |
          cd /home/app/prod/app
          source ../venv/bin/activate
          python manage.py migrate --settings=config.settings.prod

      - name: Collect static
        run: |
          cd /home/app/prod/app
          source ../venv/bin/activate
          python manage.py collectstatic --noinput --settings=config.settings.prod

      - name: Restart service
        run: sudo systemctl restart praxis
```

---

# 📚 Lições Aprendidas

## 1️⃣ Caminho absoluto é obrigatório
Systemd não perdoa erro de path.

## 2️⃣ wsgi.py define o ambiente real
Se estiver apontando para dev → produção quebra.

## 3️⃣ manage.py pode sobrescrever settings
Sempre usar `--settings=config.settings.prod` no deploy.

## 4️⃣ Gunicorn precisa estar no venv correto
Erro comum:
```
Unable to locate executable
```

## 5️⃣ DNS duplicado gera caos
Nunca manter dois registros A para o mesmo domínio.

## 6️⃣ Self-hosted runner é a forma correta
Mais seguro.
Mais previsível.
Sem abrir SSH público.

## 7️⃣ Nunca dar sudo total ao usuário do app
Permitir apenas o comando necessário.

---

# 🛡 Próximo Passo Recomendado

- Fechar porta 22 para ANY
- Liberar apenas seu IP fixo
- Instalar SSL (Let's Encrypt)

---

# 🎯 Estado Atual

✔ Deploy automático funcionando  
✔ Serviço reiniciando via workflow  
✔ DNS apontado  
✔ PostgreSQL configurado  
✔ Infra estabilizada  

---

Infra agora está profissional.
