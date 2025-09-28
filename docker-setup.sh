#!/bin/bash

echo "Останавливаем и удаляем контейнеры..."
docker compose down

echo "Запускаем контейнеры..."
docker compose up -d

sleep 5

echo "Выполняем миграции базы данных..."
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate

echo "Собираем статические файлы..."
docker compose exec backend python manage.py collectstatic --noinput

echo "Копируем статические файлы..."
docker compose exec backend cp -r /app/staticfiles/. /backend_static/static/

echo "Все операции выполнены успешно!"
