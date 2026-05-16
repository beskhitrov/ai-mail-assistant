# Sprint 1 Report: AI Mail Assistant

## Краткое описание

AI Mail Assistant — учебный FastAPI-сервис для анализа входящих писем.
Пользователь отправляет письмо через HTTP API, сервис валидирует данные,
получает структурированный анализ через LLM-слой и сохраняет письмо с
результатом анализа в PostgreSQL.

В Sprint 1 вместо реального внешнего LLM используется `FakeLLMClient`.
Он детерминированно возвращает summary, category, priority, tasks,
entities и draft_reply. Это делает MVP воспроизводимым без API-ключей и
сетевых зависимостей.

## Архитектура

Проект разделен на слои:

- `app/api` — HTTP endpoints и FastAPI dependencies;
- `app/schemas` — Pydantic-схемы входных и выходных данных;
- `app/services` — бизнес-логика анализа письма и LLM-контракт;
- `app/repositories` — сохранение данных через SQLAlchemy session;
- `app/db` — SQLAlchemy Base, session factory и ORM-модели;
- `alembic` — миграции схемы БД;
- `tests` — автоматические проверки MVP.

Основной поток:

1. Клиент вызывает `POST /api/v1/emails/analyze`.
2. FastAPI валидирует JSON через `EmailCreate`.
3. `EmailAnalyzer` вызывает `LLMClient`.
4. `FakeLLMClient` возвращает `EmailAnalysisResult`.
5. `EmailRepository` сохраняет `Email` и `EmailAnalysis`.
6. API возвращает `EmailAnalysisResponse`.

## Используемые библиотеки

- FastAPI — HTTP API.
- Uvicorn — ASGI-сервер.
- Pydantic и pydantic-settings — схемы и настройки.
- SQLAlchemy — ORM-модели и работа с БД.
- Alembic — миграции.
- psycopg2-binary — PostgreSQL driver.
- pytest — тесты.
- ruff и mypy — качество кода и типизация.
- Docker / Docker Compose — локальный запуск backend + PostgreSQL.

## Endpoints

### GET /health

Проверяет, что приложение запущено.

Ответ:

```json
{"status": "ok"}
```

### POST /api/v1/emails/analyze

Принимает письмо, анализирует его, сохраняет письмо и результат анализа.

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
    ]
  }
}
```

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

Связь: `email_analyses.email_id -> emails.id`, один-к-одному,
с каскадным удалением анализа при удалении письма.

## Роль LLM

LLM-слой изолирован за `LLMClient` Protocol. Сейчас его реализует
`FakeLLMClient`, чтобы тесты и демонстрация не зависели от внешнего API.
Во втором спринте можно добавить реальный OpenAI-compatible клиент,
не меняя FastAPI endpoint и репозиторий.

## Тестирование

Проверяются:

- health endpoint;
- Pydantic-валидация письма;
- fake LLM и извлечение задач;
- сценарий без задач;
- SQLAlchemy metadata и связи моделей;
- сохранение письма и анализа;
- rollback при ошибке сохранения;
- успешный и ошибочные сценарии API.

Команды:

```bash
pytest
ruff check .
mypy app tests alembic
alembic upgrade head --sql
```

## Запуск MVP

```bash
docker compose up --build
```

После запуска:

```bash
curl http://localhost:8000/health
```

## Ограничения Sprint 1

- используется fake LLM, а не реальный внешний API;
- нет Telegram-бота;
- нет авторизации пользователей;
- нет фоновой обработки очередей;
- Redis не подключен, потому что для Sprint 1 он не нужен.

## Дальнейшее развитие

После Sprint 1 проект можно развивать в сторону второго интерфейса,
реального LLM-провайдера, фоновой обработки и истории анализов. Эти
направления не меняют базовую архитектуру: FastAPI остается HTTP-слоем,
`EmailAnalyzer` отвечает за бизнес-логику, `LLMClient` скрывает
провайдера модели, а `EmailRepository` отвечает за PostgreSQL.
