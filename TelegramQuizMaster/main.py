import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers import start, skills, progress, achievements, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to run the bot"""
    
    # Initialize bot with default properties
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher
    dp = Dispatcher()
    
    # Include routers
    dp.include_router(start.router)
    dp.include_router(skills.router)
    dp.include_router(progress.router)
    dp.include_router(achievements.router)
    dp.include_router(admin.router)
    
    # Error handler
    @dp.error()
    async def error_handler(update, exception):
        """Global error handler"""
        logger.exception(f"Error occurred: {exception}")
        
        if hasattr(update, 'message') and update.message:
            try:
                await update.message.answer(
                    "❌ Произошла ошибка. Попробуйте еще раз или воспользуйтесь командой /start"
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")
        
        return True  # Mark as handled
    
    # Start polling
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error during polling: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
