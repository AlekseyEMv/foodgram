# Foodgram — Продуктовый помощник
![GitHub Workflow Status](https://github.com/AlekseyEMv/foodgram/actions/workflows/main.yml/badge.svg)

![Python](https://img.shields.io/badge/Python-3.9-3776AB?logo=python) 
![Django](https://img.shields.io/badge/Django-3.2.16-092E20?logo=django) 
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue?logo=postgresql) 
![Django REST Framework](https://img.shields.io/badge/Django_REST_Framework-3.12.4-blue?logo=django) 
![Gunicorn](https://img.shields.io/badge/Gunicorn-20.1.0-blue?logo=gunicorn) 
![Nginx](https://img.shields.io/badge/Nginx-blue?logo=nginx) 
![Docker](https://img.shields.io/badge/Docker-blue?logo=docker) 
![Docker Compose](https://img.shields.io/badge/Docker_Compose-blue?logo=docker) 
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-blue?logo=githubactions) 

## Описание проекта

**[Foodgram](https://foodgrammae.viewdns.net/recipes)** — это веб-приложение, где пользователи могут:
* Публиковать рецепты
* Подписываться на других пользователей
* Добавлять рецепты в избранное
* Формировать список покупок
* Скачивать список необходимых продуктов

Проект включает:
* Бэкенд на Django
* REST API
* Контейнеризацию через Docker
* Автоматизацию деплоя через GitHub Actions

## Установка и запуск

### Клонирование репозитория
```bash
git clone https://github.com/AlekseyEMv/foodgram.git
cd foodgram
```

### Подготовка окружения
Создайте файл `.env` на основе `.env.example` и настройте параметры:
* SECRET_KEY
* DEBUG
* ALLOWED_HOSTS
* Параметры базы данных

### Запуск через Docker
```bash
sudo docker-compose up
```

### Последующие действия
```bash
# Миграции
sudo docker-compose exec backend python manage.py migrate

# Сбор статических файлов
sudo docker-compose exec backend python manage.py collectstatic --noinput

# Создание суперпользователя
sudo docker-compose exec backend python manage.py createsuperuser

# Загрузка данных
sudo docker-compose exec backend python manage.py load_data_ingredients
sudo docker-compose exec backend python manage.py load_data_tags
```

## CI/CD через GitHub Actions

### Настройка секретов GitHub
Добавьте в Secrets следующие переменные:
* **DB_ENGINE**, **DB_NAME**, **DB_USER**, **DB_PASSWORD**, **DB_HOST**, **DB_PORT** — параметры БД
* **DOCKER_USERNAME**, **DOCKER_PASSWORD** — доступ к DockerHub
* **USER**, **HOST**, **PASSPHRASE**, **SSH_KEY** — параметры сервера

### Подготовка сервера
1. Подключитесь к серверу:
```bash
ssh <username>@<host>
```

2. Установите Docker:
```bash
sudo apt install docker.io
```

3. Установите Docker Compose:
```bash
sudo apt install docker-compose
```

4. Скопируйте конфигурационные файлы:
```bash
scp docker-compose.production.yml <username>@<host>:/home/<username>/foodgram/
```

5. Скопируйте файл .env на сервер, в директорию foodgram
```bash
scp docker-compose.production.yml <username>@<host>:/home/<username>/foodgram/
```

6. Запустите контейнеры в режиме демона:
```bash
sudo docker-compose -f docker-compose.production.yml up -d
```

## API документации
Полная документация API доступна в файле `docs/redoc.html`

## Контактная информация
* Репозиторий: [Foodgram](https://github.com/AlekseyEMv/foodgram)
* Сайт: <https://foodgrammae.viewdns.net>
* Автор: [AlekseyEMv](https://github.com/AlekseyEMv)