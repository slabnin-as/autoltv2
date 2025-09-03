# AutoLT v2

Flask-приложение для автоматизации работы с задачами Jira и управления работами Jenkins с возможностью планирования выполнения.

## Возможности

- 🔍 Поиск и синхронизация задач из Jira
- 💾 Сохранение данных задач в PostgreSQL
- ⚙️ Управление работами Jenkins
- ⏰ Планирование запуска работ по расписанию (cron)
- 🌐 Веб-интерфейс для просмотра и редактирования данных
- 📊 Панель управления с статистикой

## Быстрый старт

1. Клонируйте репозиторий
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Настройте окружение:
   ```bash
   cp .env.example .env
   # Отредактируйте .env файл с вашими настройками
   ```

4. Настройте базу данных:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. Запустите приложение:
   ```bash
   python run.py
   ```

## Настройка

Скопируйте `.env.example` в `.env` и заполните следующие параметры:

### Jira
- `JIRA_URL` - URL вашего Jira (например, https://company.atlassian.net)
- `JIRA_USERNAME` - Ваш email в Jira
- `JIRA_API_TOKEN` - API токен (создается в настройках Jira)

### Jenkins  
- `JENKINS_URL` - URL Jenkins сервера
- `JENKINS_USERNAME` - Имя пользователя Jenkins
- `JENKINS_TOKEN` - API токен Jenkins

### База данных
- `DATABASE_URL` - Строка подключения к PostgreSQL

## Архитектура

Приложение построено с использованием Blueprint-ов Flask для масштабируемости:

- **Модели** (`app/models/`) - SQLAlchemy модели для работы с БД
- **Сервисы** (`app/services/`) - Бизнес-логика интеграции с внешними системами  
- **Маршруты** (`app/blueprints/`) - Flask маршруты для веб-интерфейса и API
- **Планировщик** - APScheduler для выполнения задач по расписанию

## API

Приложение предоставляет REST API для интеграции:

- `GET /api/stats` - Общая статистика
- `GET /api/tasks` - Список задач Jira
- `PUT /api/tasks/{id}` - Обновление задачи
- `GET /api/jobs` - Список работ Jenkins
- `PUT /api/jobs/{id}` - Обновление работы