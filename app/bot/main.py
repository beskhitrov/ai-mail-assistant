"""Telegram bot entrypoint."""

import asyncio
from importlib import import_module
from typing import Any

from app.bot.formatter import format_analysis_for_telegram
from app.bot.service import analyze_telegram_email
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories.email_repository import RepositoryError
from app.services.llm_client import LLMClientError
from app.services.llm_factory import LLMClientConfigurationError


START_MESSAGE = (
    "Отправьте текст письма, и я верну summary, tasks, category, priority "
    "и draft reply."
)


class TelegramBotConfigurationError(Exception):
    """Raised when Telegram bot settings are invalid."""


def create_dispatcher() -> Any:
    """Create aiogram dispatcher with handlers."""
    aiogram = _import_aiogram()
    router = aiogram.Router()

    @router.message(aiogram.filters.CommandStart())
    async def handle_start(message: Any) -> None:
        """Send short usage message."""
        await message.answer(START_MESSAGE)

    @router.message(aiogram.F.text)
    async def handle_email_text(message: Any) -> None:
        """Analyze Telegram text message as email."""
        text = message.text or ""
        user_id = message.from_user.id if message.from_user else 0

        db = SessionLocal()
        try:
            response = analyze_telegram_email(text, user_id, db_session=db)
        except (LLMClientError, LLMClientConfigurationError):
            await message.answer("Не удалось проанализировать письмо через LLM.")
            return
        except RepositoryError:
            await message.answer("Анализ выполнен, но сохранить результат не удалось.")
            return
        finally:
            db.close()

        await message.answer(format_analysis_for_telegram(response))

    dispatcher = aiogram.Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


async def run_bot() -> None:
    """Run Telegram bot polling."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        msg = "TELEGRAM_BOT_TOKEN is required to run Telegram bot"
        raise TelegramBotConfigurationError(msg)

    aiogram = _import_aiogram()
    bot = aiogram.Bot(token=settings.telegram_bot_token)
    dispatcher = create_dispatcher()
    await dispatcher.start_polling(bot)


def _import_aiogram() -> Any:
    """Import aiogram lazily so tests do not require Telegram package import."""
    try:
        return import_module("aiogram")
    except ImportError as exc:
        msg = "aiogram package is required to run Telegram bot"
        raise TelegramBotConfigurationError(msg) from exc


if __name__ == "__main__":
    asyncio.run(run_bot())
