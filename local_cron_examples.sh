#!/bin/bash
# Example cron jobs for AutoLT v2 automation

# Добавьте эти строки в crontab (crontab -e)

echo "=== AutoLT v2 Cron Examples ==="
echo ""
echo "Добавьте следующие строки в cron (crontab -e):"
echo ""

echo "# 1. Полная автоматизация (синхронизация + планирование) каждые 15 минут"
echo "*/15 * * * * curl -X POST http://localhost:5000/tasks/api/auto-sync-and-schedule"
echo ""

echo "# 2. Только синхронизация каждые 10 минут"  
echo "*/10 * * * * curl -X POST http://localhost:5000/tasks/api/auto-sync-only"
echo ""

echo "# 3. Только планирование каждые 30 минут"
echo "*/30 * * * * curl -X POST http://localhost:5000/tasks/api/auto-schedule-only"
echo ""

echo "# 4. Полная автоматизация каждый час в 5 минут"
echo "5 * * * * curl -X POST http://localhost:5000/tasks/api/auto-sync-and-schedule"
echo ""

echo "# 5. Ежедневная синхронизация в 9:00"
echo "0 9 * * * curl -X POST http://localhost:5000/tasks/api/auto-sync-only"
echo ""

echo "# 6. Планирование каждый будний день в 18:30 (перед началом слотов)"
echo "30 18 * * 1-5 curl -X POST http://localhost:5000/tasks/api/auto-schedule-only"
echo ""

echo "=== Команды для управления cron ==="
echo "crontab -e     # редактировать cron jobs"
echo "crontab -l     # показать текущие cron jobs" 
echo "crontab -r     # удалить все cron jobs"
echo ""

echo "=== Тестирование endpoint'ов ==="
echo "curl -X POST http://localhost:5000/tasks/api/auto-sync-and-schedule"
echo "curl -X POST http://localhost:5000/tasks/api/auto-sync-only"
echo "curl -X POST http://localhost:5000/tasks/api/auto-schedule-only"