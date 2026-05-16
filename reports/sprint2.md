# Sprint 2 Report: AI Mail Assistant

## Краткое описание

AI Mail Assistant — учебный сервис на Python для интеллектуальной
обработки входящих писем. Во втором спринте проект доведен до
demo-ready состояния: письмо можно отправить через HTTP API или
Telegram-бота, анализ выполняется через fake LLM или OpenAI-compatible
API, результаты сохраняются в PostgreSQL и доступны через историю.
Дополнительно добавлены Makefile-команды, CI-проверки и Sphinx-
документация, чтобы проект было проще проверять и демонстрировать.

Главный сценарий проекта — Inbox Zero с помощью AI:

- кратко пересказать письмо;
- выделить задачи;
- определить категорию и приоритет;
- подготовить черновик ответа;
- сохранить результат для последующего просмотра.

## Что добавлено во втором спринте

- OpenAI-compatible LLM client с переключением через `LLM_PROVIDER`.
- Redis/RQ очередь и отдельный worker для фонового анализа.
- Async API: постановка анализа в очередь и проверка статуса job.
- API истории сохраненных анализов.
- Telegram-бот на aiogram.
- Docker Compose demo-запуск для backend, PostgreSQL, Redis и worker.
- Отдельный Docker Compose profile для Telegram-бота.
- Makefile с едиными командами для запуска, проверок и сборки docs.
- GitHub Actions CI для тестов, линтинга, typecheck, Docker Compose
  config, Alembic SQL и Sphinx.
- Sphinx-документация с автодокументацией по основным модулям.
- GitHub Pages workflow для публикации HTML-документации.

## Архитектура

Проект разделен на слои:

- `app/api` — HTTP endpoints и FastAPI dependencies;
- `app/bot` — Telegram-интерфейс;
- `app/schemas` — Pydantic-схемы входных и выходных данных;
- `app/services` — бизнес-логика анализа и LLM-клиенты;
- `app/repositories` — работа с сохранением и чтением данных;
- `app/db` — SQLAlchemy session, Base и ORM-модели;
- `app/core` — настройки и очередь;
- `app/workers` — фоновые RQ-задачи;
- `alembic` — миграции БД;
- `docs` — Sphinx-документация проекта;
- `.github/workflows` — CI и публикация документации;
- `tests` — автоматические проверки.

Основная идея архитектуры: HTTP API, Telegram-бот и worker используют
один сервисный слой. Анализ письма находится в `EmailAnalyzer`, работа с
LLM скрыта за `LLMClient`, а доступ к БД вынесен в `EmailRepository`.

## Основные сценарии

### Синхронный HTTP-анализ

1. Клиент вызывает `POST /api/v1/emails/analyze`.
2. FastAPI валидирует JSON через `EmailCreate`.
3. `EmailAnalyzer` вызывает настроенный `LLMClient`.
4. `EmailRepository` сохраняет письмо и анализ.
5. API возвращает `EmailAnalysisResponse`.

### Асинхронный HTTP-анализ

1. Клиент вызывает `POST /api/v1/emails/analyze-async`.
2. API кладет задачу в Redis/RQ очередь.
3. Клиент получает `job_id`.
4. Worker выполняет `analyze_email_job`.
5. Worker использует `EmailAnalyzer` и `EmailRepository`.
6. Клиент проверяет статус через `GET /api/v1/jobs/{job_id}`.

### Telegram-анализ

1. Пользователь отправляет текст письма боту.
2. Бот превращает сообщение в `EmailCreate`.
3. Бот вызывает тот же `EmailAnalyzer`.
4. Результат форматируется в Telegram-сообщение.
5. При наличии DB session результат сохраняется через `EmailRepository`.

## Используемые библиотеки

- FastAPI — HTTP API.
- Uvicorn — ASGI-сервер.
- Pydantic и pydantic-settings — схемы и настройки.
- SQLAlchemy — ORM и запросы к PostgreSQL.
- Alembic — миграции БД.
- psycopg2-binary — PostgreSQL driver.
- httpx — OpenAI-compatible HTTP client и тестовые mock-запросы.
- redis — подключение к Redis.
- rq — очередь фоновых задач и worker.
- aiogram — Telegram-бот.
- pytest — автоматические тесты.
- ruff и mypy — качество кода и типизация.
- Sphinx и sphinx-autodoc-typehints — HTML-документация и
  автодокументация Python-модулей.
- Docker / Docker Compose — воспроизводимый demo-запуск.
- GitHub Actions — CI и публикация документации.

## Endpoints

### GET /health

Проверяет, что backend запущен.

Ответ:

```json
{"status": "ok"}
```

### POST /api/v1/emails/analyze

Синхронно анализирует письмо, сохраняет письмо и анализ.

Пример запроса:

```json
{
  "sender": "teacher@example.com",
  "recipient": "student@example.com",
  "subject": "Срочно подготовить отчет",
  "body": "Нужно подготовить отчет по проекту."
}
```

Ключевые поля ответа:

```json
{
  "analysis": {
    "summary": "Срочно подготовить отчет: Нужно подготовить отчет по проекту.",
    "category": "work",
    "priority": "high",
    "tasks": [
      {
        "title": "Нужно подготовить отчет по проекту",
        "priority": "high"
      }
    ],
    "draft_reply": "Здравствуйте! Спасибо за письмо. Я изучу информацию и вернусь с ответом."
  }
}
```

### POST /api/v1/emails/analyze-async

Кладет письмо в очередь фонового анализа.

Ответ:

```json
{
  "job_id": "some-rq-job-id",
  "status": "queued"
}
```

### GET /api/v1/jobs/{job_id}

Возвращает статус фоновой задачи. Если задача завершена, поле `result`
содержит результат анализа.

Возможные статусы зависят от RQ: `queued`, `started`, `finished`,
`failed`.

### GET /api/v1/emails

Возвращает историю сохраненных писем и анализов.

Поддерживает параметры:

- `limit` — от 1 до 100;
- `offset` — от 0.

### GET /api/v1/emails/{email_id}

Возвращает одно сохраненное письмо и связанный анализ. Если записи нет,
возвращается HTTP 404.

## Схема базы данных

### emails

- `id`;
- `sender`;
- `recipient`;
- `subject`;
- `body`;
- `received_at`;
- `created_at`.

### email_analyses

- `id`;
- `email_id`;
- `summary`;
- `category`;
- `priority`;
- `tasks`;
- `entities`;
- `draft_reply`;
- `created_at`.

Связь: `email_analyses.email_id -> emails.id`, один-к-одному.
Для demo-ready истории этого достаточно: каждое новое письмо создает
новую строку `emails` и связанную строку `email_analyses`.

## Роль LLM

LLM-слой изолирован за `LLMClient` Protocol.

Реализации:

- `FakeLLMClient` — deterministic клиент для тестов, локального запуска
  и защиты без API-ключей;
- `OpenAICompatibleLLMClient` — клиент для OpenAI-compatible
  `/chat/completions` API.

Выбор клиента выполняется через переменные окружения:

```env
LLM_PROVIDER=fake
```

или:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

`EmailAnalyzer` не меняется при переключении провайдера.

## Redis и очередь

Redis используется как брокер для RQ. Очередь называется
`email-analysis` по умолчанию.

Фоновая задача:

```text
app.workers.tasks.analyze_email_job
```

Она:

1. получает сериализованное письмо;
2. валидирует его через `EmailCreate`;
3. вызывает `EmailAnalyzer`;
4. сохраняет результат через `EmailRepository`;
5. возвращает сериализованный `EmailAnalysisResponse`.

## Telegram-бот

Telegram-бот реализован на aiogram. Для MVP достаточно простого
сценария:

1. пользователь отправляет текст письма;
2. бот строит `EmailCreate`;
3. бот вызывает сервис анализа;
4. бот возвращает summary, category, priority, tasks и draft reply.

Бот запускается отдельно:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here python -m app.bot.main
```

или через Docker Compose profile:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here docker compose --profile telegram up --build
```

## Docker Compose demo

Стандартный запуск:

```bash
docker compose up --build
```

Поднимает:

- `backend`;
- `postgres`;
- `redis`;
- `worker`.

Telegram-бот вынесен в отдельный profile, чтобы обычный demo-запуск не
требовал Telegram-токен.

## Команды разработки

Для повторяемых действий добавлен `Makefile`.

Основные команды:

```bash
make install
make test
make lint
make typecheck
make check
make alembic-sql
make docs
make up
make up-telegram
make down
```

`make check` объединяет основные локальные проверки: тесты, ruff, mypy,
проверку обычного Docker Compose config и config с Telegram profile.

## CI/CD и документация

CI настроен в `.github/workflows/ci.yml`.

Workflow запускается на push в `dev`, `main`, `feature*` и на pull
request в `dev` или `main`. Он выполняет:

- установку зависимостей;
- `make check`;
- `make alembic-sql`;
- `make docs`.

Документация находится в директории `docs` и собирается через Sphinx:

```bash
make docs
```

HTML-результат создается в `docs/_build/html` и не коммитится.

Отдельный workflow `.github/workflows/docs.yml` собирает документацию
при push в `main` или ручном запуске и публикует ее через GitHub Pages.
Это закрывает demo-ready часть проекта: код можно проверить через CI, а
структуру сервиса можно посмотреть в опубликованной документации.

## Проверка

Команды:

```bash
make check
make alembic-sql
make docs
```

Результат проверок:

- pytest — 35 passed;
- ruff — без ошибок;
- mypy — без ошибок;
- docker compose config — без ошибок;
- docker compose --profile telegram config — без ошибок.
- alembic upgrade head --sql — SQL генерируется без ошибок;
- sphinx-build — HTML-документация собирается без ошибок.

## Ограничения Sprint 2

- Нет авторизации и пользовательского кабинета.
- Telegram-бот поддерживает только простой сценарий отправки текста.
- История анализов хранится как один анализ на одно письмо.
- Нет отдельного web UI.
- Реальный OpenAI-compatible режим требует внешний API-ключ.
- GitHub Pages требует включить Pages source `GitHub Actions` в
  настройках репозитория.

## Возможные направления развития

- Добавить пользователей и авторизацию.
- Поддержать несколько анализов для одного письма.
- Добавить web UI для истории и просмотра задач.
- Добавить дедлайны и календарную интеграцию.
- Расширить Telegram-бота командами `/history` и `/status`.
