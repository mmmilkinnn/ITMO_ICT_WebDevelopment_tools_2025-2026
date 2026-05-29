# Лабораторная работа 3


## Состав

- `api` - основное FastAPI-приложение.
- `parser` - отдельный FastAPI-сервис парсера.
- `db` - PostgreSQL.
- `redis` - брокер сообщений и backend результатов Celery.
- `celery_worker` - воркер для фонового парсинга.
- `celery_beat` - периодические задачи.

## Запуск

```bash
cd lab3
docker compose up --build
```

Сервисы:

- API: `http://localhost:8000/docs`
- Parser service: `http://localhost:8001/docs`
- PostgreSQL снаружи: `localhost:5433`
- Redis снаружи: `localhost:6380`

## Проверка прямого вызова парсера

```bash
curl -X POST http://localhost:8000/parser/parse \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://devpost.com/hackathons\"}"
```

## Проверка очереди Celery

Создать задачу:

```bash
curl -X POST http://localhost:8000/parser/tasks \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://devpost.com/hackathons\"}"
```

Проверить статус:

```bash
curl http://localhost:8000/parser/tasks/<task_id>
```

## Проверка данных

Список сохраненных записей:

```bash
curl http://localhost:8000/hackathons
```

## Периодические задачи

В `app/celery_app.py` настроена задача `parse_default_sources_task`.
`celery_beat` запускает ее раз в час и ставит в обработку стандартный список источников.
