# 🚀 Publicação do Projeto Praxis
Django + VPS Hostinger + Azure DevOps + Gunicorn + Nginx

Este documento descreve o processo completo de publicação da aplicação Praxis em produção utilizando pipeline automatizado.

---

# 🧱 Arquitetura Final

```
Azure DevOps (Trigger na master)
        │
        ▼
Azure Agent (ubuntu-latest)
        │
        │ SSH
        ▼
VPS Hostinger
        │
        ├── /home/praxis/praxis_crm
        │       ├── venv
        │       ├── manage.py
        │       ├── requirements.txt
        │       └── ...
        │
        ├── Gunicorn (unix socket)
        │       └── praxis.sock
        │
        └── Nginx (porta 80)
                └── Proxy para socket
```

---

# 1️⃣ Configuração do Azure DevOps

## 🔑 1.1 Criar PAT (Personal Access Token)

No Azure DevOps:

1. Clicar na foto de perfil (canto superior direito)
2. User Settings
3. Personal Access Tokens
4. New Token

Permissões mínimas:
- Code (Read & Write)

Salvar o token.

---

## 🔐 1.2 Gerar chave SSH na VPS

Na VPS:

```bash
ssh-keygen -t rsa -b 4096 -C "vps-deploy"
```

Arquivos gerados:

```
~/.ssh/id_rsa
~/.ssh/id_rsa.pub
```

---

## 🔗 1.3 Adicionar chave pública no Azure Repos

Copiar conteúdo de:

```bash
cat ~/.ssh/id_rsa.pub
```

No Azure DevOps:

- Repos
- Project Settings
- SSH Public Keys
- Add

Colar chave pública.

---

## 🔧 1.4 Configurar remote do Git para SSH

```bash
git remote set-url origin git@ssh.dev.azure.com:v3/ORG/PROJETO/praxis_crm
```

Testar:

```bash
git fetch
```

Se funcionar sem pedir senha, está correto.

---

## 🔌 1.5 Criar Service Connection SSH no Azure

No Azure DevOps:

1. Project Settings
2. Service Connections
3. New Service Connection
4. SSH

Preencher:

- Host: IP da VPS
- Port: 22
- Username: praxis
- Private Key: conteúdo do ~/.ssh/id_rsa
- Passphrase: se houver

Salvar como:
```
praxis-vps-ssh
```

---

# 2️⃣ Preparação da VPS

## Atualizar sistema

```bash
sudo apt update
sudo apt upgrade -y
```

## Instalar dependências

```bash
sudo apt install python3 python3-venv python3-pip nginx git -y
```

---

# 3️⃣ Clonar projeto

```bash
cd /home/praxis
git clone git@ssh.dev.azure.com:v3/ORG/PROJETO/praxis_crm
```

---

# 4️⃣ Criar ambiente virtual

```bash
cd /home/praxis/praxis_crm
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

Adicionar gunicorn ao requirements.txt.

---

# 5️⃣ Configurar systemd

Arquivo:

```bash
sudo nano /etc/systemd/system/praxis.service
```

Conteúdo:

```ini
[Unit]
Description=Praxis Django App
After=network.target

[Service]
User=praxis
Group=www-data
WorkingDirectory=/home/praxis/praxis_crm

ExecStart=/home/praxis/praxis_crm/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/home/praxis/praxis_crm/praxis.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Ativar:

```bash
sudo systemctl daemon-reload
sudo systemctl start praxis
sudo systemctl enable praxis
```

---

# 6️⃣ Configurar Nginx

Arquivo:

```bash
sudo nano /etc/nginx/sites-available/praxis
```

Conteúdo:

```nginx
server {
    listen 80;
    server_name 187.77.37.217;

    location /static/ {
        root /home/praxis/praxis_crm;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/praxis/praxis_crm/praxis.sock;
    }
}
```

Ativar:

```bash
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/praxis /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

# 7️⃣ Pipeline Azure DevOps

Arquivo `azure-pipelines.yml`:

```yaml
trigger:
- master

pool:
  vmImage: 'ubuntu-latest'

stages:
- stage: Deploy
  displayName: "Deploy para VPS"
  jobs:
  - job: DeployJob
    steps:
    - task: SSH@0
      inputs:
        sshEndpoint: 'praxis-vps-ssh'
        runOptions: 'commands'
        commands: |
          set -e

          git -C /home/praxis/praxis_crm fetch --all
          git -C /home/praxis/praxis_crm reset --hard origin/master

          source /home/praxis/praxis_crm/venv/bin/activate

          pip install --upgrade pip
          pip install --no-cache-dir -r /home/praxis/praxis_crm/requirements.txt

          python /home/praxis/praxis_crm/manage.py migrate --noinput
          python /home/praxis/praxis_crm/manage.py collectstatic --noinput

          sudo systemctl restart praxis
```

---

# ❓ FAQ – Problemas Enfrentados

## 502 Bad Gateway

### Gunicorn não instalado
```
venv/bin/gunicorn: No such file
```
Solução:
```
pip install gunicorn
```

---

### Caminho errado (case sensitive)
```
praxis_CRM vs praxis_crm
```
Linux diferencia maiúsculas.

---

### Permissão do socket
Garantir:
```
Group=www-data
```
no systemd.

---

## 400 Bad Request

Problema:
```
ALLOWED_HOSTS
```

Solução:
```python
ALLOWED_HOSTS = ["IP_DO_SERVIDOR"]
```

---

## venv/bin/activate: No such file

Criar ambiente:
```
python3 -m venv venv
```

---

# 🎯 Resultado Final

Deploy automatizado funcionando com:

- Azure DevOps
- SSH seguro
- Gunicorn via socket
- Nginx como proxy reverso
- Serviço gerenciado por systemd

Infraestrutura estável e pronta para produção.
