# AutoLT v2 Deployment Guide

## Системные требования

- Ubuntu/Debian/CentOS сервер
- Python 3.8+
- PostgreSQL 12+
- Nginx (рекомендуется)
- Supervisor (для автозапуска)

## Установка на сервере

### 1. Подготовка системы

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib nginx supervisor git curl -y

# Создание пользователя для приложения (опционально)
sudo useradd -m -s /bin/bash autolt
sudo su - autolt
```

### 2. Клонирование проекта

```bash
# В домашней директории пользователя
cd /home/autolt  # или /opt/autoltv2
git clone https://github.com/slabnin-as/autoltv2.git
cd autoltv2

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Настройка PostgreSQL

```bash
# Вход в PostgreSQL как суперпользователь
sudo -u postgres psql

-- Создание базы данных и пользователя
CREATE DATABASE autoltv2;
CREATE SCHEMA IF NOT EXISTS autoltv2;
CREATE USER autolt_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE autoltv2 TO autolt_user;
GRANT ALL ON SCHEMA autoltv2 TO autolt_user;
GRANT CREATE ON SCHEMA autoltv2 TO autolt_user;

-- Выход
\q
```

### 4. Настройка окружения

```bash
# Создание .env файла
cp .env.example .env

# Редактирование .env
nano .env
```

**Содержимое .env файла:**

```env
# Flask
SECRET_KEY=very_secure_secret_key_change_this
FLASK_ENV=production
FLASK_APP=run.py

# Database
DATABASE_URL=postgresql://autolt_user:secure_password_here@localhost/autoltv2?options=-csearch_path%3Dautoltv2%2Cpublic

# JIRA Configuration
JIRA_URL=https://your-jira-domain.atlassian.net
JIRA_USERNAME=your-jira-email@company.com
JIRA_API_TOKEN=your_jira_api_token_here

# Jenkins Configuration  
JENKINS_URL=https://your-jenkins-server.com
JENKINS_USERNAME=your_jenkins_username
JENKINS_TOKEN=your_jenkins_api_token

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0
```

### 5. Инициализация базы данных

```bash
# Активация виртуального окружения
source venv/bin/activate

# Создание таблиц
python3 -c "
from app import create_app, db
from app.models import *
app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized successfully!')
"
```

### 6. Настройка Gunicorn

```bash
# Создание конфигурационного файла
nano gunicorn.conf.py
```

**gunicorn.conf.py:**

```python
bind = "127.0.0.1:5000"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

### 7. Настройка Supervisor

```bash
# Создание конфигурации supervisor
sudo nano /etc/supervisor/conf.d/autoltv2.conf
```

**/etc/supervisor/conf.d/autoltv2.conf:**

```ini
[program:autoltv2]
command=/home/autolt/autoltv2/venv/bin/gunicorn -c gunicorn.conf.py run:app
directory=/home/autolt/autoltv2
user=autolt
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/autoltv2.log
environment=PATH="/home/autolt/autoltv2/venv/bin"
```

```bash
# Перезапуск supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start autoltv2
sudo supervisorctl status
```

### 8. Настройка Nginx

```bash
# Создание конфигурации nginx
sudo nano /etc/nginx/sites-available/autoltv2
```

**/etc/nginx/sites-available/autoltv2:**

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Статические файлы
    location /static/ {
        alias /home/autolt/autoltv2/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Логи
    access_log /var/log/nginx/autoltv2_access.log;
    error_log /var/log/nginx/autoltv2_error.log;
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/autoltv2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Настройка автоматизации (Cron)

```bash
# Редактирование crontab
crontab -e

# Добавление автоматических задач
# Полная автоматизация каждые 15 минут
*/15 * * * * curl -s -X POST http://localhost:5000/tasks/api/auto-sync-and-schedule > /dev/null 2>&1

# Или только в рабочее время
30 18 * * 1-5 curl -s -X POST http://localhost:5000/tasks/api/auto-schedule-only > /dev/null 2>&1
```

### 10. SSL сертификат (рекомендуется)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com

# Автообновление сертификата
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Проверка работоспособности

```bash
# Проверка статуса сервисов
sudo systemctl status nginx
sudo supervisorctl status autoltv2

# Проверка логов
sudo tail -f /var/log/autoltv2.log
sudo tail -f /var/log/nginx/autoltv2_error.log

# Тестирование API
curl http://your-domain.com/
curl -X POST http://your-domain.com/tasks/api/auto-sync-only
```

## Полезные команды

```bash
# Перезапуск приложения
sudo supervisorctl restart autoltv2

# Обновление кода
cd /home/autolt/autoltv2
git pull origin master
sudo supervisorctl restart autoltv2

# Просмотр логов
sudo tail -f /var/log/autoltv2.log

# Проверка процессов
sudo supervisorctl status
ps aux | grep gunicorn
```

## Безопасность

1. **Файрвол:**
```bash
sudo ufw allow 22
sudo ufw allow 80  
sudo ufw allow 443
sudo ufw enable
```

2. **Регулярные обновления:**
```bash
sudo apt update && sudo apt upgrade -y
```

3. **Резервное копирование базы данных:**
```bash
pg_dump -U autolt_user -h localhost autoltv2 > backup_$(date +%Y%m%d).sql
```

## Мониторинг

- Логи приложения: `/var/log/autoltv2.log`  
- Логи nginx: `/var/log/nginx/autoltv2_*.log`
- Статус сервисов: `sudo supervisorctl status`
- Проверка автоматизации: просмотр cron логов в `/var/log/syslog`

Приложение будет доступно по адресу `http://your-domain.com`