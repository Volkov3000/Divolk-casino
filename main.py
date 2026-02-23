# watermark_id: wm_11_9_58033d8d-5461-492a-ba00-b3c719b3f9fd
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, LOG_CHAT_ID, ADMIN_ID, logger
from database import db
from utils import crypto
from handlers.common import register_common_handlers

async def shutdown():
    await crypto.close()
    db.close()
    logger.info("Bot shutdown complete")

async def main():
    logger.info("=" * 50)
    logger.info("🐝 BeeCube Casino Bot v10.0 - ПОЛНАЯ ВЕРСИЯ")
    logger.info(f"Admin ID: {ADMIN_ID}")
    logger.info(f"Log Chat ID: {LOG_CHAT_ID}")
    logger.info("=" * 50)
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    crypto.set_bot(bot)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    register_common_handlers(dp)
    
    asyncio.create_task(crypto.check_pending_invoices())
    
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown()

if __name__ == "__main__":
    asyncio.run(main())