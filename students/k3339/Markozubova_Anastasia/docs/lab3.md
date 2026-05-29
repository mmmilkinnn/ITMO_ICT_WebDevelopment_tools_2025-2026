# Лабораторная Работа 3

## Тема

Упаковка FastAPI-приложения в Docker, работа с источниками данных и очереди.

> Выполнила: Маркозубова Анастасия

## Цель работы

Цель лабораторной работы - упаковать FastAPI-приложение, базу данных и парсер в Docker, настроить вызов парсера через API и добавить выполнение парсинга через очередь задач.

## Использованные технологии

- Python 3.12
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy
- Docker
- Docker Compose
- Redis
- Celery
- Requests

## Структура проекта

```text
lab3/
├── app/
│   ├── api_service.py
│   ├── celery_app.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── parser_logic.py
│   └── parser_service.py
├── Dockerfile.api
├── Dockerfile.parser
├── docker-compose.yml
├── README.md
└── requirements.txt
```

## Описание реализации

В работе приложение разделено на несколько сервисов:

- `api` - основное FastAPI-приложение;
- `parser` - отдельный FastAPI-сервис для парсинга;
- `db` - база данных PostgreSQL;
- `redis` - брокер сообщений для Celery;
- `celery_worker` - обработчик фоновых задач;
- `celery_beat` - сервис для периодических задач.

Все сервисы описаны в файле:

```text
lab3/docker-compose.yml
```

Основной API запускается из файла `Dockerfile.api` на порту `8000`.
Parser-сервис запускается из файла `Dockerfile.parser` на порту `8001`.

## Работа с базой данных

Подключение к базе данных находится в файле:

```text
lab3/app/database.py
```

Модели описаны в файле:

```text
lab3/app/models.py
```

Для сохранения результатов парсинга используется таблица `hackathons`. В нее сохраняются:

- `title` - заголовок страницы;
- `source_url` - URL источника;
- `description` - описание источника;
- `status` - статус записи;
- `parser_approach` - способ запуска парсера.

## Parser-сервис

Parser-сервис находится в файле:

```text
lab3/app/parser_service.py
```

Основная ручка parser-сервиса:

```text
POST /parse
```

Она принимает URL, вызывает функцию парсинга и сохраняет результат в PostgreSQL.

Логика парсинга находится в файле:

```text
lab3/app/parser_logic.py
```

Parser отправляет HTTP-запрос к переданному URL, получает HTML-страницу, извлекает содержимое тега `<title>` и сохраняет результат в таблицу `hackathons`.

## Основной API

Основное FastAPI-приложение находится в файле:

```text
lab3/app/api_service.py
```

Реализованные ручки:

| Метод | Ручка | Назначение |
|---|---|---|
| `GET` | `/` | проверка работы API |
| `GET` | `/hackathons` | получение сохраненных записей |
| `POST` | `/parser/parse` | синхронный вызов parser-сервиса |
| `POST` | `/parser/tasks` | асинхронный запуск парсинга через Celery |
| `GET` | `/parser/tasks/{task_id}` | проверка статуса Celery-задачи |

При синхронном вызове ручка `/parser/parse` отправляет запрос в parser-сервис и ждет результат.

При асинхронном вызове ручка `/parser/tasks` ставит задачу в очередь Celery и сразу возвращает `task_id`.

## Celery и Redis

Настройка Celery находится в файле:

```text
lab3/app/celery_app.py
```

Redis используется как брокер задач и хранилище результатов. Celery worker забирает задачи из Redis и выполняет их в фоне.

В проекте есть две задачи:

- `parse_url_task` - парсит один URL;
- `parse_default_sources_task` - парсит стандартный список источников.

Для периодического запуска используется Celery Beat. В расписании настроен запуск задачи `parse_default_sources_task` каждый час.

## Запуск проекта

Перейти в папку лабораторной работы:

```bash
cd students/k3339/Markozubova_Anastasia/lab3
```

Запустить контейнеры:

```bash
docker compose up --build
```

После запуска доступны:

| Сервис | Адрес |
|---|---|
| Основной API | `http://localhost:8000/docs` |
| Parser service | `http://localhost:8001/docs` |
| PostgreSQL | `localhost:5433` |
| Redis | `localhost:6380` |

Проверить контейнеры:

```bash
docker compose ps
```

## Проверка работы

Проверка основного API:

```text
GET http://localhost:8000/
```

Список сохраненных записей:

```text
GET http://localhost:8000/hackathons
```

Синхронный запуск парсера:

```json
POST http://localhost:8000/parser/parse

{
  "url": "https://devpost.com/hackathons"
}
```

Асинхронный запуск через Celery:

```json
POST http://localhost:8000/parser/tasks

{
  "url": "https://mlh.io/seasons/2026/events"
}
```

Проверка статуса задачи:

```text
GET http://localhost:8000/parser/tasks/{task_id}
```

Прямой вызов parser-сервиса:

```json
POST http://localhost:8001/parse

{
  "url": "https://www.kaggle.com/competitions"
}
```

## Вывод

В ходе лабораторной работы было создано приложение из нескольких Docker-контейнеров. Основной API принимает запросы пользователя, отдельный parser-сервис выполняет парсинг страниц, PostgreSQL хранит результаты, Redis используется для очереди задач, а Celery выполняет парсинг в фоне.

Был реализован синхронный вызов parser-сервиса через `/parser/parse` и асинхронный вызов через `/parser/tasks`. Результаты парсинга сохраняются в таблицу `hackathons` и проверяются через ручку `/hackathons`.
