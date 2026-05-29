# Лабораторная Работа 3

## Тема

Упаковка FastAPI-приложения в Docker, работа с источниками данных и очереди.

> Выполнила: Маркозубова Анастасия

## Цель работы

Целью лабораторной работы является упаковка FastAPI-приложения, базы данных и парсера в Docker, а также настройка взаимодействия между сервисами. В работе реализован прямой вызов парсера через HTTP и асинхронный запуск парсинга через очередь задач Celery с брокером Redis.

В лабораторной работе выполнены три основные части:

- упаковка FastAPI-приложения, parser-сервиса и PostgreSQL в Docker;
- вызов parser-сервиса из основного FastAPI-приложения;
- вызов parser-сервиса через очередь Celery и Redis.

## Использованные технологии

- Python 3.12
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy
- Pydantic
- Requests
- Docker
- Docker Compose
- Redis
- Celery
- Celery Beat

## Структура проекта

```text
lab3/
├── app/
│   ├── __init__.py
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

Проект разделен на несколько сервисов. Основное приложение принимает запросы пользователя, parser-сервис выполняет парсинг страниц, PostgreSQL хранит результаты, Redis используется для очереди задач, Celery worker выполняет фоновые задачи, а Celery Beat запускает периодический парсинг.

## Состав Docker Compose

Все сервисы описаны в файле:

```text
lab3/docker-compose.yml
```

В `docker-compose.yml` настроены следующие контейнеры:

| Сервис | Назначение |
|---|---|
| `db` | база данных PostgreSQL |
| `redis` | брокер сообщений и хранилище результатов Celery |
| `parser` | отдельное FastAPI-приложение для парсинга |
| `api` | основное FastAPI-приложение |
| `celery_worker` | обработчик фоновых задач |
| `celery_beat` | запуск периодических задач по расписанию |

Сервис `db` использует образ `postgres:16-alpine`. Для него задана база данных `hackathon_lab3`, пользователь `postgres` и пароль `1234`. Внешний порт базы данных:

```text
localhost:5433
```

Внутри Docker-сети база доступна по адресу:

```text
db:5432
```

Для PostgreSQL добавлен `healthcheck`, чтобы остальные сервисы начинали работу после готовности базы данных.

Сервис `redis` использует образ `redis:7-alpine`. Он доступен внутри Docker-сети как:

```text
redis:6379
```

Снаружи Redis проброшен на порт:

```text
localhost:6380
```

Сервис `parser` собирается из файла `Dockerfile.parser` и запускается на порту `8001`. Он подключается к базе данных через переменную окружения:

```text
DATABASE_URL=postgresql+psycopg://postgres:1234@db:5432/hackathon_lab3
```

Сервис `api` собирается из файла `Dockerfile.api` и запускается на порту `8000`. Для связи с другими контейнерами используются переменные окружения:

```text
DATABASE_URL=postgresql+psycopg://postgres:1234@db:5432/hackathon_lab3
PARSER_SERVICE_URL=http://parser:8001
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

Сервис `celery_worker` запускает Celery worker командой:

```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

Сервис `celery_beat` запускает планировщик периодических задач:

```bash
celery -A app.celery_app.celery_app beat --loglevel=info
```

## Dockerfile для API и parser-сервиса

Для основного API используется файл:

```text
lab3/Dockerfile.api
```

В нем указан базовый образ:

```dockerfile
FROM python:3.12-slim
```

Далее устанавливаются зависимости из `requirements.txt`, копируется папка `app` и запускается Uvicorn:

```dockerfile
CMD ["uvicorn", "app.api_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

Для parser-сервиса используется файл:

```text
lab3/Dockerfile.parser
```

Он устроен так же, но запускает другое FastAPI-приложение:

```dockerfile
CMD ["uvicorn", "app.parser_service:app", "--host", "0.0.0.0", "--port", "8001"]
```

Таким образом, основной API и parser работают как два независимых HTTP-сервиса.

## Конфигурация приложения

Настройки вынесены в файл:

```text
lab3/app/config.py
```

В классе `Settings` хранятся:

- название проекта;
- строка подключения к PostgreSQL;
- адрес parser-сервиса;
- адрес Redis для Celery broker;
- адрес Redis для Celery result backend.

Значения читаются из переменных окружения. Это удобно для Docker Compose, потому что внутри контейнеров нельзя обращаться к соседним сервисам через `localhost`. Вместо этого используются имена сервисов: `db`, `parser`, `redis`.

## Модель данных

Модели находятся в файле:

```text
lab3/app/models.py
```

В проекте используются две ORM-модели:

- `User`;
- `Hackathon`.

Модель `User` нужна для связи с хакатонами. В схеме поле `organizer_id` является обязательным, поэтому для записей, созданных парсером, используется служебный организатор:

```text
lab3-parser@example.com
```

Модель `Hackathon` хранит данные о найденном источнике:

| Поле | Что хранится |
|---|---|
| `title` | заголовок HTML-страницы |
| `source_url` | URL, который был передан в парсер |
| `description` | краткое описание источника и способа парсинга |
| `start_date` | дата создания записи |
| `end_date` | дата создания записи + 7 дней |
| `status` | значение `parsed` |
| `parser_approach` | способ запуска парсера |
| `organizer_id` | служебный пользователь-организатор |

Для сохранения результата используется функция:

```python
create_parsed_hackathon(session, url, title, approach)
```

Она создает запись в таблице `hackathons`, выполняет `session.commit()` и возвращает созданный объект.

## Подключение к базе данных

Работа с базой данных находится в файле:

```text
lab3/app/database.py
```

Подключение создается через SQLAlchemy:

```python
engine = create_engine(settings.DATABASE_URL, future=True)
```

Функция `prepare_database()` создает таблицы:

```python
Base.metadata.create_all(bind=engine)
```

Также она создает служебного организатора для записей, которые добавляет parser.

Функция `get_db()` используется в основном API как FastAPI dependency. Через нее эндпоинты получают сессию базы данных.

## Parser-сервис

Отдельное приложение парсера находится в файле:

```text
lab3/app/parser_service.py
```

В нем создается отдельный экземпляр FastAPI:

```python
app = FastAPI(title="Lab 3 Parser Service")
```

При старте parser-сервиса вызывается `prepare_database()`. Это нужно, чтобы таблицы были созданы до обработки запросов.

У parser-сервиса есть две ручки:

| Метод | URL | Назначение |
|---|---|---|
| `GET` | `/` | проверка, что parser-сервис работает |
| `POST` | `/parse` | запуск парсинга указанного URL |

Ручка `POST /parse` принимает JSON:

```json
{
  "url": "https://devpost.com/hackathons"
}
```

Для поля `url` используется тип `HttpUrl`, поэтому FastAPI проверяет корректность ссылки.

После получения запроса parser вызывает:

```python
parse_and_save_url(str(payload.url), "http-parser-service")
```

Если внешний сайт недоступен или возвращает ошибку, parser-сервис возвращает HTTP 500.

## Логика парсинга

Основная логика находится в файле:

```text
lab3/app/parser_logic.py
```

В файле есть список стандартных источников:

```python
DEFAULT_URLS = [
    "https://devpost.com/hackathons",
    "https://hackathon.com/",
    "https://mlh.io/seasons/2026/events",
    "https://www.kaggle.com/competitions",
    "https://www.spaceappschallenge.org/",
]
```

Они используются для периодической задачи Celery Beat.

Для извлечения заголовка страницы используется класс `TitleParser`, который наследуется от стандартного `HTMLParser`. Он находит содержимое тега `<title>`.

Функция `extract_title(html)` получает HTML-страницу и возвращает ее заголовок. Если заголовок не найден, возвращается строка:

```text
Untitled hackathon source
```

Главная функция:

```python
parse_and_save_url(url, approach)
```

Выполняет следующие действия:

1. отправляет GET-запрос к переданному URL;
2. проверяет успешность ответа через `raise_for_status()`;
3. извлекает `<title>` из HTML;
4. открывает сессию PostgreSQL;
5. сохраняет запись в таблицу `hackathons`;
6. возвращает JSON с результатом.

Пример ответа:

```json
{
  "message": "Parsing completed",
  "url": "https://devpost.com/hackathons",
  "title": "New & upcoming hackathons - Devpost",
  "hackathon_id": 17
}
```

Парсер в этой работе не извлекает все карточки хакатонов со страницы. Он сохраняет заголовок страницы как результат парсинга. Этого достаточно для демонстрации связки: внешний источник данных, parser-сервис, PostgreSQL, основной API и очередь задач.

## Основное FastAPI-приложение

Основное приложение находится в файле:

```text
lab3/app/api_service.py
```

В нем создается FastAPI-приложение:

```python
app = FastAPI(title=settings.PROJECT_NAME)
```

При старте приложения вызывается `prepare_database()`, чтобы база была готова к работе.

Входная схема для запросов парсинга:

```python
class ParseRequest(BaseModel):
    url: HttpUrl
```

Схема ответа для сохраненных хакатонов:

```python
class HackathonResponse(BaseModel):
```

Она возвращает:

- `id`;
- `title`;
- `source_url`;
- `status`;
- `parser_approach`.

### `GET /`

Проверяет, что основное API работает.

Ответ:

```json
{
  "message": "Lab 3 API is running"
}
```

### `GET /hackathons`

Возвращает список записей из таблицы `hackathons`.

Запрос выполняется через SQLAlchemy:

```python
select(Hackathon).order_by(Hackathon.id.desc())
```

Эта ручка используется для проверки, что результат парсинга действительно сохранился в PostgreSQL.

### `POST /parser/parse`

Это синхронный вызов parser-сервиса.

Основной API принимает JSON:

```json
{
  "url": "https://devpost.com/hackathons"
}
```

После этого API делает HTTP-запрос в parser-сервис:

```python
requests.post(
    f"{settings.PARSER_SERVICE_URL}/parse",
    json={"url": str(payload.url)},
    timeout=30,
)
```

В Docker Compose `PARSER_SERVICE_URL` равен:

```text
http://parser:8001
```

То есть основной API не парсит страницу сам, а обращается к отдельному контейнеру `parser`. После завершения парсинга API возвращает результат клиенту.

Если parser-сервис недоступен, основной API возвращает ошибку `502 Bad Gateway`.

### `POST /parser/tasks`

Это асинхронный запуск парсинга через Celery.

API принимает такой же JSON:

```json
{
  "url": "https://mlh.io/seasons/2026/events"
}
```

Задача отправляется в очередь:

```python
task = parse_url_task.delay(str(payload.url))
```

Метод `delay()` не выполняет парсинг сразу в процессе API. Он отправляет задачу в Redis, после чего `celery_worker` забирает ее и выполняет в фоне.

Ответ API:

```json
{
  "task_id": "id-задачи",
  "status": "queued"
}
```

### `GET /parser/tasks/{task_id}`

Эта ручка проверяет состояние фоновой задачи.

Для получения статуса используется:

```python
AsyncResult(task_id, app=celery_app)
```

Возможные статусы:

- `PENDING`;
- `STARTED`;
- `SUCCESS`;
- `FAILURE`.

Если задача завершилась успешно, в ответ добавляется поле `result`.

Пример успешного ответа:

```json
{
  "task_id": "id-задачи",
  "status": "SUCCESS",
  "result": {
    "message": "Parsing completed",
    "url": "https://mlh.io/seasons/2026/events",
    "title": "Major League Hacking",
    "hackathon_id": 18
  }
}
```

## Настройка Celery

Celery настроен в файле:

```text
lab3/app/celery_app.py
```

Создание Celery-приложения:

```python
celery_app = Celery(
    "lab3_parser_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
```

В качестве broker используется Redis:

```text
redis://redis:6379/0
```

В качестве result backend также используется Redis:

```text
redis://redis:6379/1
```

Задача `parse_url_task` получает URL и вызывает parser-сервис:

```python
@celery_app.task(name="parse_url_task")
def parse_url_task(url: str) -> dict:
```

Внутри задачи выполняется POST-запрос:

```python
requests.post(
    f"{settings.PARSER_SERVICE_URL}/parse",
    json={"url": url},
    timeout=60,
)
```

То есть асинхронный режим работает так:

1. клиент отправляет запрос в API;
2. API кладет задачу в Redis;
3. Celery worker забирает задачу;
4. worker вызывает parser-сервис;
5. parser сохраняет данные в PostgreSQL;
6. результат задачи сохраняется в Redis;
7. клиент проверяет статус по `task_id`.

## Периодические задачи

В `celery_app.py` также настроена периодическая задача:

```python
@celery_app.task(name="parse_default_sources_task")
def parse_default_sources_task() -> list[dict]:
```

Она запускает парсинг стандартных источников из списка `DEFAULT_URLS`.

Расписание задается через `beat_schedule`:

```python
celery_app.conf.beat_schedule = {
    "parse-default-hackathon-sources-hourly": {
        "task": "parse_default_sources_task",
        "schedule": crontab(minute=0),
    },
}
```

Это означает, что Celery Beat запускает задачу каждый час в нулевую минуту.

## Как запустить проект

Перейти в папку лабораторной работы:

```bash
cd students/k3339/Markozubova_Anastasia/lab3
```

Запустить все сервисы:

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

Проверить список контейнеров:

```bash
docker compose ps
```

Посмотреть логи parser-сервиса:

```bash
docker compose logs parser
```

Посмотреть логи Celery worker:

```bash
docker compose logs celery_worker
```

## Проверка через Swagger

Основной Swagger находится по адресу:

```text
http://localhost:8000/docs
```

### Проверка основного API

Выполнить:

```text
GET /
```

Ожидаемый ответ:

```json
{
  "message": "Lab 3 API is running"
}
```

### Проверка списка сохраненных записей

Выполнить:

```text
GET /hackathons
```

Если записей еще нет, вернется пустой список:

```json
[]
```

После парсинга в списке появятся сохраненные записи.

### Проверка синхронного вызова parser-сервиса

Выполнить:

```text
POST /parser/parse
```

Тело запроса:

```json
{
  "url": "https://devpost.com/hackathons"
}
```

Пример ответа:

```json
{
  "message": "Parsing completed",
  "url": "https://devpost.com/hackathons",
  "title": "New & upcoming hackathons - Devpost",
  "hackathon_id": 17
}
```

После этого нужно снова выполнить:

```text
GET /hackathons
```

Так можно проверить, что запись появилась в PostgreSQL.

### Проверка асинхронного вызова через Celery

Выполнить:

```text
POST /parser/tasks
```

Тело запроса:

```json
{
  "url": "https://mlh.io/seasons/2026/events"
}
```

Пример ответа:

```json
{
  "task_id": "6a7e8c6e-9d3b-4c2a-a7b4-111111111111",
  "status": "queued"
}
```

Скопировать `task_id` и выполнить:

```text
GET /parser/tasks/{task_id}
```

Если задача уже завершилась, будет ответ:

```json
{
  "task_id": "6a7e8c6e-9d3b-4c2a-a7b4-111111111111",
  "status": "SUCCESS",
  "result": {
    "message": "Parsing completed",
    "url": "https://mlh.io/seasons/2026/events",
    "title": "Major League Hacking",
    "hackathon_id": 18
  }
}
```

После этого снова выполнить:

```text
GET /hackathons
```

Новая запись должна быть в списке.

## Проверка parser-сервиса напрямую

Swagger parser-сервиса находится по адресу:

```text
http://localhost:8001/docs
```

Проверить работу сервиса:

```text
GET /
```

Ответ:

```json
{
  "message": "Parser service is running"
}
```

Вызвать parser напрямую:

```text
POST /parse
```

Тело запроса:

```json
{
  "url": "https://www.kaggle.com/competitions"
}
```

Пример ответа:

```json
{
  "message": "Parsing completed",
  "url": "https://www.kaggle.com/competitions",
  "title": "Competitions",
  "hackathon_id": 19
}
```

Этот сценарий показывает, что parser является отдельным сервисом и может принимать HTTP-запросы независимо от основного API.

## Что показывать на защите

На защите удобно идти в таком порядке:

1. Открыть `docker-compose.yml` и показать сервисы `db`, `redis`, `parser`, `api`, `celery_worker`, `celery_beat`.
2. Показать `Dockerfile.api` и `Dockerfile.parser`, объяснить, что это два разных FastAPI-приложения.
3. Открыть `app/parser_service.py` и показать ручку `POST /parse`.
4. Открыть `app/parser_logic.py` и показать функцию `parse_and_save_url`.
5. Открыть `app/api_service.py` и показать ручки `/parser/parse`, `/parser/tasks`, `/parser/tasks/{task_id}` и `/hackathons`.
6. Открыть `app/celery_app.py` и показать Celery task, Redis broker и расписание Celery Beat.
7. Запустить проект через `docker compose up --build`.
8. В Swagger выполнить синхронный парсинг через `POST /parser/parse`.
9. Проверить сохранение результата через `GET /hackathons`.
10. Выполнить асинхронный парсинг через `POST /parser/tasks`.
11. Проверить статус задачи через `GET /parser/tasks/{task_id}`.
12. Еще раз проверить `GET /hackathons`.

## Вывод

В ходе лабораторной работы было создано приложение из нескольких Docker-контейнеров. Основной FastAPI-сервис принимает запросы пользователя, отдельный parser-сервис выполняет парсинг страниц, PostgreSQL хранит результаты, Redis используется как брокер очереди, Celery worker выполняет задачи в фоне, а Celery Beat запускает периодический парсинг по расписанию.

Был реализован синхронный сценарий, когда API сразу вызывает parser-сервис и возвращает результат клиенту. Также был реализован асинхронный сценарий, когда API ставит задачу в очередь Celery и возвращает `task_id`, по которому можно проверить статус выполнения. Результаты обоих вариантов сохраняются в таблицу `hackathons`.
