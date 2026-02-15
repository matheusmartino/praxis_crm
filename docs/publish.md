# 🚀 Deploy Django em Produção (VPS Hostinger)

Deploy definitivo do Praxis CRM  
Estrutura atual validada e funcional.

---

# 📁 Estrutura Oficial do Servidor

Diretório base:

```
/home/app/prod
```

Estrutura:

```
/home/app/prod
│
├── app/                # Projeto Django (manage.py aqui)
│   ├── manage.py
│   ├── config/
│   ├── apps/
│   └── staticfiles/
│
├── venv/               # Ambiente virtual
├── logs/
└── praxis.sock         # Criado pelo gunicorn
```

---

# 🐍 1️⃣ Ambiente Virtual

Criado manualmente:

```bash
cd /home/app/prod
python3 -m venv venv
```

Ativar:

```bash
source venv/bin/activate
```

Instalar dependências:

```bash
cd app
pip install --upgrade pip
pip install -r requirements.txt
```

---

# 🗄 2️⃣ Banco PostgreSQL

Exemplo funcional:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "praxis_db",
        "USER": "usuario_prod",
        "PASSWORD": "SENHA_CORRETA_AQUI",
        "HOST": "127.0.0.1",
        "PORT": "5432",
        "CONN_MAX_AGE": 60,
    }
}
```

Aplicar migrations:

```bash
python manage.py migrate
```

---

# 🧾 3️⃣ Configuração prod.py Essencial

```python
DEBUG = False

ALLOWED_HOSTS = [
    "187.77.37.217",
    "praxisapp.com.br",
    ".praxisapp.com.br",
]

CSRF_TRUSTED_ORIGINS = [
    "http://praxisapp.com.br",
    "http://www.praxisapp.com.br",
]
```

---

# 📦 4️⃣ Arquivos Estáticos

```bash
python manage.py collectstatic --noinput
```

Devem ir para:

```
/home/app/prod/app/staticfiles/
```

---

# 🔫 5️⃣ Gunicorn (systemd)

Arquivo:

```
/etc/systemd/system/praxis.service
```

Conteúdo:

```
[Unit]
Description=Praxis Django App
After=network.target

[Service]
User=app
Group=www-data
WorkingDirectory=/home/app/prod/app
ExecStart=/home/app/prod/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/home/app/prod/praxis.sock \
          config.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

Recarregar e iniciar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable praxis
sudo systemctl restart praxis
```

Verificar:

```bash
sudo systemctl status praxis
```

---

# 🌐 6️⃣ Nginx

Arquivo:

```
/etc/nginx/sites-available/praxis
```

Conteúdo:

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
        proxy_pass http://unix:/home/app/prod/praxis.sock;
    }
}
```

Ativar:

```bash
sudo ln -s /etc/nginx/sites-available/praxis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

# 🌍 7️⃣ DNS

No Hostinger:

Tipo A  
Nome: @  
Conteúdo: 187.77.37.217  

Tipo CNAME  
Nome: www  
Conteúdo: praxisapp.com.br  

---

# 🔎 8️⃣ Diagnóstico Rápido

### Ver nginx:
```bash
sudo systemctl status nginx
```

### Ver gunicorn:
```bash
sudo systemctl status praxis
```

### Ver socket:
```bash
ls -la /home/app/prod/praxis.sock
```

### Ver logs nginx:
```bash
sudo tail -n 50 /var/log/nginx/error.log
```

---

# 🧠 Lições Aprendidas

1. 502 quase sempre é socket errado ou gunicorn parado.
2. Caminho absoluto salva vidas.
3. `WorkingDirectory` errado quebra tudo.
4. `ALLOWED_HOSTS` causa erro 400.
5. `CSRF_TRUSTED_ORIGINS` causa 400 silencioso.
6. Static errado quebra layout.
7. Não confiar em variável dinâmica no deploy.
8. Sempre testar com `curl localhost`.

---

# 🏁 Estado Final

✔ VPS rodando  
✔ PostgreSQL ativo  
✔ Gunicorn como serviço  
✔ Nginx proxyando  
✔ DNS apontado  
✔ Deploy funcional  

---

# 🔜 Próximo Passo

Criar ambiente:

```
dev.praxisapp.com.br
```

Separando:

```
/home/app/dev
/home/app/prod
```

Com services diferentes:

- praxis-prod.service
- praxis-dev.service
