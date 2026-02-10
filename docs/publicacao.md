# 🚀 Deploy em VPS com Django + Azure DevOps

Este documento descreve o **processo completo de publicação** de uma aplicação Django em uma VPS Linux, utilizando **Azure DevOps com self-hosted agent** para CI/CD.

O objetivo é ter um deploy:
- previsível
- repetível
- sem acesso manual em produção

---

## 📐 Arquitetura

```
Azure DevOps Pipeline
        ↓
Self-hosted Agent (VPS)
        ↓
Git pull / install / migrate
        ↓
Gunicorn (Django)
        ↓
Nginx (80 / 443)
```

---

## 1️⃣ Pré-requisitos

### VPS
- Ubuntu 22.04 LTS
- Acesso SSH
- IP público
- Portas 80 e 443 liberadas

### Projeto
- Django funcional
- Repositório Git
- `requirements.txt` atualizado

---

## 2️⃣ Acesso inicial à VPS

```bash
ssh root@IP_DA_VPS
apt update && apt upgrade -y
```

---

## 3️⃣ Criar usuário de deploy

Nunca rode produção como `root`.

```bash
adduser deploy
usermod -aG sudo deploy
exit
ssh deploy@IP_DA_VPS
```

---

## 4️⃣ Instalar dependências do sistema

```bash
sudo apt install -y \
  python3 python3-pip python3-venv \
  nginx git curl unzip build-essential
```

---

## 5️⃣ Estrutura do projeto

```bash
mkdir ~/apps
cd ~/apps
git clone https://github.com/seuusuario/seuprojeto.git
cd seuprojeto
```

---

## 6️⃣ Criar ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 7️⃣ Variáveis de ambiente

Adicionar no `~/.bashrc` do usuário `deploy`:

```bash
export DJANGO_SETTINGS_MODULE=seuprojeto.settings
export SECRET_KEY='sua-chave-secreta'
export DEBUG=False
export ALLOWED_HOSTS=seusite.com,IP_DA_VPS
```

```bash
source ~/.bashrc
```

---

## 8️⃣ Ajustes no Django

No `settings.py`:

```python
DEBUG = False
STATIC_ROOT = BASE_DIR / "staticfiles"
```

Executar:

```bash
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

---

## 9️⃣ Teste manual com Gunicorn

```bash
gunicorn seuprojeto.wsgi:application --bind 0.0.0.0:8000
```

Acessar:
```
http://IP_DA_VPS:8000
```

Se funcionar, interrompa com `Ctrl+C`.

---

## 🔟 Gunicorn como serviço (systemd)

Criar o serviço:

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=gunicorn
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/home/deploy/apps/seuprojeto
ExecStart=/home/deploy/apps/seuprojeto/venv/bin/gunicorn \
          seuprojeto.wsgi:application \
          --bind unix:/run/gunicorn.sock

[Install]
WantedBy=multi-user.target
```

Ativar:

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

---

## 1️⃣1️⃣ Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/seuprojeto
```

```nginx
server {
    listen 80;
    server_name seusite.com IP_DA_VPS;

    location /static/ {
        root /home/deploy/apps/seuprojeto;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Ativar o site:

```bash
sudo ln -s /etc/nginx/sites-available/seuprojeto /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

## 1️⃣2️⃣ Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 1️⃣3️⃣ Azure DevOps – Self-hosted Agent

### Criar usuário do agent

```bash
sudo adduser azagent
sudo usermod -aG sudo azagent
su - azagent
```

### Criar Agent Pool
No Azure DevOps:
- Organization Settings
- Agent Pools
- Criar pool: `vps-production`

### Criar PAT
- User Settings → Personal Access Tokens
- Permissão: **Agent Pools (Read & manage)**

### Instalar o agent

```bash
mkdir ~/agent && cd ~/agent
wget https://vstsagentpackage.azureedge.net/agent/3.xx.x/vsts-agent-linux-x64-3.xx.x.tar.gz
tar zxvf vsts-agent-linux-x64-*.tar.gz
./config.sh
```

Respostas sugeridas:
```
Server URL: https://dev.azure.com/SUA_ORG
Authentication: PAT
Agent pool: vps-production
Run agent as service: Y
```

---

## 1️⃣4️⃣ Permissões para deploy

```bash
sudo usermod -aG deploy azagent
sudo visudo
```

Adicionar:

```bash
azagent ALL=(ALL) NOPASSWD: /bin/systemctl restart gunicorn
```

---

## 1️⃣5️⃣ Pipeline Azure DevOps (YAML)

```yaml
trigger:
  - main

pool:
  name: vps-production

steps:
  - checkout: self

  - script: |
      cd /home/deploy/apps/seuprojeto
      git pull
      source venv/bin/activate
      pip install -r requirements.txt
      python manage.py migrate
      python manage.py collectstatic --noinput
      sudo systemctl restart gunicorn
    displayName: Deploy Django em VPS
```

---

## ✅ Checklist final

- [ ] VPS configurada
- [ ] Django rodando com Gunicorn
- [ ] Nginx ativo
- [ ] Agent Azure DevOps online
- [ ] Pipeline executando com sucesso
- [ ] Deploy sem acesso manual

---

## 🧠 Boas práticas

- Nunca rodar produção como root
- Um agent por ambiente (staging ≠ produção)
- Token com expiração curta
- Backup antes de migrations
- Se está funcionando, não mexa sem motivo

---

## 📌 Observação final

Este modelo prioriza **simplicidade, estabilidade e controle**.  
Escalabilidade e orquestração vêm depois — quando o produto justificar.
