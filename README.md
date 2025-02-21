# # Foodgram - продуктовый помощник
![Foodgram CI](https://github.com/raidert63/foodgram/actions/workflows/main.yml/badge.svg) \
«Фудграм» — сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Стэк используемых технологий
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org)
[![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)](https://www.django-rest-framework.org/)
[![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)](https://nginx.org/)
[![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)](https://docs.github.com/en/actions)

## Разворачивание проекта
* ### Разворачиваем с использованием образов в [DockerHUB](https://hub.docker.com)
    Cоздаём папку проекта `foodgram` и переходим в нее:

    ```bash
    mkdir foodgram && cd foodgram
    ```

    В папку проекта копируем (или создаём) файлы `docker-compose.production.yml` `nginx.conf` из папки `infra`. Также необходим файл `.env` (пример ниже). Запускаем проект командой:

    ```bash
    sudo docker compose -f docker-compose.production.yml up
    ```

    Будут загружены последние образы, созданы и запущены контейнеры, созданы необходимые тома и сеть.
* ### Разворачиваем используя [Github](https://github.com/)
    Клонируем себе репозиторий и переходим в него: 

    ```bash 
    git clone git@github.com:4its/foodgram-project-react.git
    ```

    Выполняем запуск:

    ```bash
    sudo docker compose -f docker-compose.yml up
    ```
    ### После запуска необходимо применить миграции, а также копирование статики
    Статика frontend'а собирается автоматически, после чего контейнер будет остановлен.\
    Необходимо выполнить следующие команды: 
    
    ```bash
    sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py migrate
    sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py collectstatic
    sudo docker compose -f [имя-файла-docker-compose.yml] exec backend cp -r /app/collected_static/. /backend_static/static/
    ```
    Также можно(рекомендуется) единоразово выполнить импорт базовых данных:
    ```bash
    sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py import_tags
    sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py import_ingredients
    ```

## Файл .env
  Пример файла .env c переменными окружения, необходимыми для запуска
    
  ```sh
    DEBUG=True
    SECRET_KEY=CHANGE_IT_BEFORE_USE_IN_PRODUCTION
    ALLOWED_HOSTS=localhost,127.0.0.1,YOUR.DOMAIN,
    LANGUAGE_CODE=ru-RU
    TIME_ZONE=Europe/Moscow

    # Database settings block
    USE_SQLITE=     True/False(whatever else you want to)
    POSTGRES_DB=    NAME OF YOUR DB
    POSTGRES_DB_HOST= NAME OF YOUR DB HOST (ex. 127.0.0.1 or db)
    POSTGRES_DB_PORT= PORT TO ACCESS DB
    POSTGRES_PASSWORD= YOUR DB PASSWORD
    POSTGRES_USER= YOUR DB USER
   ```
## Документация API проекта
  После запуска проекта, можно ознакопиться с endpoint'ами прокта и их возможностями.
  Документация будет доступна по адресу: `имя_сервера/api/docs/`
  

## Проект доступен в сети интернет: 
* **https://foodgram63.ddns.net/**
* **158.160.24.20**

## Доступ:
* **review@review.ru**
* **review**
