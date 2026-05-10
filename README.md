# AI Mail Assistant

## Идея проекта

**AI Mail Assistant** — это небольшой сервис на Python для интеллектуальной обработки электронной почты.  
Он подключается к почтовому ящику, получает письма, анализирует их с помощью LLM и помогает пользователю быстрее работать с входящей почтой.

Цель проекта — показать, как современные AI-инструменты можно встроить в привычный рабочий сценарий: чтение писем, выделение главного, извлечение задач и подготовка ответа.

Проект ориентирован на сценарий “Inbox Zero с помощью AI”:
- письмо автоматически кратко пересказывается;
- из текста выделяются задачи, сроки и важные сущности;
- письма можно классифицировать по категориям;
- пользователю предлагается черновик ответа.

Проект рассчитан на реализацию одним разработчиком в рамках учебного курса MIPT Python.

## Технологический стек

Проект строится как небольшой микросервис с контейнеризацией.

### Базовая архитектура
- **FastAPI** — HTTP API
- **PostgreSQL** — хранение писем, результатов анализа, пользователей и истории запросов
- **Docker / Docker Compose** — запуск окружения
- **SQLAlchemy** — ORM для работы с базой данных
- **Alembic** — миграции базы данных
- **Pydantic** — схемы валидации данных
- **aiogram** — Telegram-бот как дополнительный интерфейс
- **LLM API** или локальная модель — анализ текста писем
- **Redis** — опционально для очередей, кэша или хранения состояний бота

### Результат первого спринта
К 26 апреля должен быть готов MVP, который:
- запускается локально в Docker;
- принимает письмо через API;
- анализирует его через LLM;
- сохраняет результаты в БД;
- возвращает summary, category, priority и tasks.

### Результат второго спринта
К 10 мая проект должен уметь:
- принимать письма через API и Telegram;
- генерировать summary;
- извлекать задачи;
- строить draft reply;
- хранить историю анализов;
- выглядеть как законченный demo-ready сервис.

## Используемые библиотеки

Ниже список библиотек, которые планируется использовать в проекте.

### Backend
- **fastapi** — создание REST API
- **uvicorn** — ASGI-сервер для запуска FastAPI
- **pydantic** — валидация входных и выходных данных
- **sqlalchemy** — ORM для PostgreSQL
- **alembic** — миграции базы данных
- **psycopg2-binary** или **asyncpg** — драйвер PostgreSQL

### Telegram
- **aiogram** — Telegram-бот

### AI / LLM
- **openai** или совместимый клиент — вызов LLM
- **httpx** — HTTP-запросы к внешним AI API
- **tenacity** — повторные попытки при нестабильных запросах к модели

### Работа с фоном и кэшем
- **redis** — кэш, временные данные, состояния
- **celery** или **rq** — фоновые задачи, если понадобится асинхронная обработка писем

### Конфигурация и удобство разработки
- **python-dotenv** — загрузка переменных окружения
- **pydantic-settings** — управление конфигурацией
- **pytest** — тестирование
- **pytest-asyncio** — тесты для асинхронного кода
- **black** — форматирование
- **ruff** — линтинг
- **mypy** — статический анализ типов

### Контейнеризация
- **Docker**
- **Docker Compose**

## Текущий статус разработки

Репозиторий находится на этапе `feature14`: Sprint 2 demo-ready сервис
собран в воспроизводимое Docker Compose окружение.

На этом шаге реализованы основные требования второго спринта:

- локальный запуск через Docker Compose;
- `GET /health`;
- `POST /api/v1/emails/analyze`;
- `POST /api/v1/emails/analyze-async`;
- `GET /api/v1/jobs/{job_id}`;
- `GET /api/v1/emails`;
- `GET /api/v1/emails/{email_id}`;
- анализ письма через fake LLM или OpenAI-compatible API;
- сохранение письма и результата анализа в PostgreSQL;
- Redis/RQ очередь и worker для фонового анализа;
- Telegram-бот на aiogram;
- история анализов;
- тесты ключевого сценария;
- отчет `reports/sprint1.md`.

Эти части добавляются отдельными небольшими feature-ветками.

## Локальный запуск через Docker Compose

По умолчанию Compose запускает backend, PostgreSQL, Redis и RQ worker в
fake LLM-режиме:

```bash
docker compose up --build
```

Сервисы:

- `backend` — FastAPI API;
- `postgres` — база данных;
- `redis` — брокер очереди;
- `worker` — RQ worker для фонового анализа;
- `telegram-bot` — Telegram-интерфейс, запускается отдельным profile.

При старте backend применяет миграции:

```bash
alembic upgrade head
```

После запуска API доступен на `http://localhost:8000`.

Проверьте health-check:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

Остановить окружение:

```bash
docker compose down
```

Остановить окружение и удалить volume PostgreSQL:

```bash
docker compose down -v
```

Запустить Telegram-бота вместе с окружением:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here docker compose --profile telegram up --build
```

## Настройка LLM

По умолчанию используется deterministic fake-клиент:

```env
LLM_PROVIDER=fake
```

Это удобно для тестов, локального запуска и защиты без внешних ключей.

Для реального OpenAI-compatible API:

```bash
LLM_PROVIDER=openai \
OPENAI_API_KEY=your_api_key_here \
OPENAI_BASE_URL=https://api.openai.com/v1 \
OPENAI_MODEL=gpt-4o-mini \
docker compose up --build
```

`EmailAnalyzer` не зависит от конкретного провайдера. Клиент выбирается
через общий `LLMClient` interface и фабрику.

## Локальный запуск без Docker

Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Запустите приложение:

```bash
uvicorn app.main:app --reload
```

Проверьте health-check:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## Анализ письма через API

После запуска приложения можно отправить тестовое письмо:

```bash
curl -X POST http://localhost:8000/api/v1/emails/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "teacher@example.com",
    "recipient": "student@example.com",
    "subject": "Срочно подготовить отчет",
    "body": "Нужно подготовить отчет по проекту."
  }'
```

Endpoint возвращает структурированный результат анализа:

```json
{
  "email": {
    "sender": "teacher@example.com",
    "recipient": "student@example.com",
    "subject": "Срочно подготовить отчет",
    "body": "Нужно подготовить отчет по проекту.",
    "received_at": null
  },
  "analysis": {
    "summary": "Срочно подготовить отчет: Нужно подготовить отчет по проекту.",
    "category": "work",
    "priority": "high",
    "tasks": [
      {
        "title": "Нужно подготовить отчет по проекту",
        "description": null,
        "deadline": null,
        "assignee": null,
        "priority": "high"
      }
    ],
    "entities": {
      "people": [],
      "organizations": [],
      "dates": []
    },
    "draft_reply": "Здравствуйте! Спасибо за письмо. Я изучу информацию и вернусь с ответом."
  }
}
```

Важно: для реального запуска endpoint с сохранением нужен доступный
PostgreSQL и примененная миграция Alembic. В тестах БД подменяется fake
session, поэтому они не требуют живую базу.

Для локального запуска endpoint с сохранением нужен PostgreSQL, доступный
по `DATABASE_URL`, и примененная миграция:

```bash
alembic upgrade head
```

## Асинхронный анализ через очередь

Поставить письмо в Redis/RQ очередь:

```bash
curl -X POST http://localhost:8000/api/v1/emails/analyze-async \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "teacher@example.com",
    "recipient": "student@example.com",
    "subject": "Срочно подготовить отчет",
    "body": "Нужно подготовить отчет по проекту."
  }'
```

Пример ответа:

```json
{"job_id":"some-rq-job-id","status":"queued"}
```

Проверить статус:

```bash
curl http://localhost:8000/api/v1/jobs/some-rq-job-id
```

Если задача завершена, `result` содержит тот же формат, что и
`POST /api/v1/emails/analyze`.

## История анализов

Получить список сохраненных анализов:

```bash
curl "http://localhost:8000/api/v1/emails?limit=50&offset=0"
```

Получить один элемент истории:

```bash
curl http://localhost:8000/api/v1/emails/1
```

История хранится в существующих таблицах `emails` и `email_analyses`.
Каждое новое письмо создает новую запись письма и связанную запись
анализа.

## Telegram-бот

Бот принимает текст письма и возвращает:

- summary;
- category;
- priority;
- tasks;
- draft reply.

Локальный запуск:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here python -m app.bot.main
```

Через Docker Compose:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here docker compose --profile telegram up --build
```

Telegram-бот не дублирует анализ. Он использует `EmailAnalyzer`,
`LLMClient` factory и `EmailRepository`.

## Команды разработки

Для удобства проверки и demo-запуска добавлен `Makefile`.

```bash
make install
make test
make lint
make typecheck
make compose-config
make compose-telegram-config
make check
make up
make up-telegram
make down
```

`make check` запускает тесты, ruff, mypy и проверку Docker Compose
конфигурации.

## Проверка проекта

```bash
make check
```

Проверить fake-анализатор можно отдельной командой:

```bash
python -c "from app.schemas import EmailCreate; from app.services import EmailAnalyzer; email = EmailCreate(sender='teacher@example.com', recipient='student@example.com', subject='Срочно подготовить отчет', body='Нужно подготовить отчет по проекту.'); print(EmailAnalyzer().analyze(email).analysis.model_dump())"
```

## Как работает fake LLM

Для локального режима используется `FakeLLMClient`, который по простым ключевым словам
детерминированно возвращает:

- `summary`;
- `category`;
- `priority`;
- `tasks`;
- `entities`;
- `draft_reply`.

Это позволяет тестировать бизнес-логику без API-ключей, сети и
нестабильных внешних ответов. Реальный OpenAI-compatible клиент
подключается через `LLM_PROVIDER=openai`, не меняя сервис
`EmailAnalyzer`.

## Модели базы данных

На этапе `feature4` добавлены две таблицы:

- `emails` — хранит исходное письмо: отправителя, получателя, тему,
  текст письма и даты;
- `email_analyses` — хранит результат анализа письма: summary,
  category, priority, tasks, entities и draft reply.

Связь между таблицами — один к одному: одно письмо имеет один результат
анализа. Внешний ключ `email_analyses.email_id` ссылается на
`emails.id` и удаляется каскадно вместе с письмом.

Проверить SQL первой миграции без подключения к PostgreSQL:

```bash
alembic upgrade head --sql
```

Когда PostgreSQL будет запущен, применить миграции можно будет так:

```bash
alembic upgrade head
```

## Репозиторий сохранения

`EmailRepository` отвечает за сохранение письма и результата анализа в
одной транзакции. Роутер FastAPI не работает с ORM-моделями напрямую:
он принимает Pydantic-схему, вызывает `EmailAnalyzer`, а затем передает
данные в репозиторий.

## Тестовое покрытие

На этапе `feature6` тесты проверяют:

- `GET /health`;
- валидацию входного письма;
- fake LLM и извлечение задач;
- сценарий без задач, где fake LLM не должен придумывать действия;
- SQLAlchemy metadata и связь `Email` / `EmailAnalysis`;
- сохранение письма и анализа через `EmailRepository`;
- rollback и `RepositoryError` при ошибке сохранения;
- успешный `POST /api/v1/emails/analyze`;
- `422` для невалидного API payload;
- `500` при ошибке сохранения анализа.
- OpenAI-compatible LLM client через `httpx.MockTransport`;
- Redis/RQ queue helpers;
- async API endpoints;
- history endpoints;
- Telegram bot service и форматирование ответа.

Тесты не требуют реального LLM API, Telegram API или живой PostgreSQL.
Для API-тестов используется dependency override и fake DB session.

## Материалы для защиты

Краткий отчет по первому спринту находится в
`reports/sprint1.md`. В нем описаны идея проекта, архитектура,
используемые библиотеки, endpoints, схема БД, роль LLM, ограничения MVP
и план второго спринта.

Отчет по второму спринту находится в `reports/sprint2.md`. В нем
описаны OpenAI-compatible LLM, Redis/RQ, async API, история анализов,
Telegram-бот и demo-ready запуск через Docker Compose.

## Ограничения MVP

- OpenAI-compatible клиент реализован, но для защиты и тестов по умолчанию
  используется `FakeLLMClient`;
- нет авторизации и пользовательского кабинета;
- Telegram-бот поддерживает простой сценарий: пользователь отправляет
  текст письма и получает результат анализа;
- связь `Email -> EmailAnalysis` пока один к одному;
- нет отдельного UI, демонстрация идет через HTTP API, Docker Compose и
  Telegram.
