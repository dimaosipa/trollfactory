#!/usr/bin/env python3
import logging
import os
from datetime import datetime
from functools import wraps
import time
import socket

from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update, ParseMode, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)
from telegram.utils.request import Request
from telegram.error import TimedOut, NetworkError, TelegramError

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log",
    filemode="a",
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# System prompt for the Ukrainian insider style
SYSTEM_PROMPT = """Ти — анонімний інсайдер, який веде телеграм-канал із витоками інформації з урядових структур та військових кіл. Ти отримуєш ексклюзивні деталі, які не озвучуються публічно, і подаєш їх у форматі аналітичних інсайдів.

Твоє завдання — взяти офіційну новину та перетворити її на телеграм-пост у стилі інсайдерської інформації.

🔹 Формат вихідного тексту:

Загадковий вступ або натяк на витік інформації.
Чітке твердження про подію, що ґрунтується на "злитих" даних.
Підтвердження через непрямі факти або заяви (але без посилань на оригінальну новину).
Аналітика: що це означає стратегічно? (у форматі нумерованого списку або коротких тез).
Завершення: натяк на подальші події або нові витоки.
🔹 Обмеження:

Не можна давати посилання на офіційні джерела.
Текст має звучати як анонімний інсайд, а не як журналістський репортаж.
Використовуй таємничий, упевнений тон, уникаючи відкритих стверджень там, де краще звучить натяк або питання."""

# Rate limiting parameters
MAX_REQUESTS_PER_MINUTE = 5
last_request_time = 0

def rate_limited(max_per_minute):
    """
    Decorator to implement rate limiting for API calls
    """
    min_interval = 60.0 / max_per_minute

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global last_request_time
            
            elapsed = time.time() - last_request_time
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                logger.info(f"Rate limit reached. Waiting for {left_to_wait:.2f} seconds")
                time.sleep(left_to_wait)
                
            last_request_time = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limited(MAX_REQUESTS_PER_MINUTE)
def generate_rewrite_with_gpt(text: str) -> str:
    """
    Generate rewritten news using GPT-4o with Ukrainian insider style
    """
    try:
        logger.info("Sending request to OpenAI API")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"{text}"
                }
            ],
            temperature=0.7,
        )
        
        rewritten_text = response.choices[0].message.content
        logger.info("Successfully received response from OpenAI API")
        return rewritten_text
        
    except Exception as e:
        logger.error(f"Error generating rewrite with GPT: {str(e)}")
        raise

def restricted(func):
    """Decorator to restrict access to the bot"""
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_USER_ID:
            logger.warning(f"Unauthorized access denied for {user_id}.")
            update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return
        return func(update, context, *args, **kwargs)
    return wrapped

@restricted
def start_command(update: Update, context: CallbackContext) -> None:
    """Handler for /start command"""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started the bot")
    update.message.reply_text(
        "Бот запущено! Пересилайте мені новини, і я перетворю їх на інсайдерські пости для вашого телеграм-каналу."
    )

@restricted
def handle_forwarded_message(update: Update, context: CallbackContext) -> None:
    """Handler for forwarded messages"""
    message = update.message
    
    # Check if the message is forwarded
    if not message.forward_date:
        message.reply_text("Це не схоже на переслане повідомлення. Будь ласка, перешліть новину для обробки.")
        return
    
    # Extract text from the forwarded message
    if not message.text:
        message.reply_text("У пересланому повідомленні не знайдено тексту.")
        return
    
    original_text = message.text
    logger.info(f"Received forwarded message: {original_text[:50]}...")
    
    try:
        # Send a status message
        logger.info("Sending status message to user")
        status_message = message.reply_text("Обробка вашого запиту...")
        
        # Generate the rewritten text
        logger.info("Generating rewritten text")
        rewritten_text = generate_rewrite_with_gpt(original_text)
        
        # Post to the channel
        try:
            logger.info(f"Posting rewritten message to channel {TELEGRAM_CHANNEL_ID}")
            context.bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=rewritten_text,
                parse_mode=ParseMode.HTML
            )
            
            logger.info(f"Published rewritten message to channel {TELEGRAM_CHANNEL_ID}")
            
            # Notify the user of success
            status_message.edit_text("✅ Повідомлення було переписано та опубліковано у каналі!")
        
        except TelegramError as telegram_error:
            error_msg = f"Помилка публікації у телеграм: {str(telegram_error)}"
            logger.error(error_msg)
            status_message.edit_text(f"❌ {error_msg}")
            
    except Exception as e:
        error_msg = f"Помилка обробки повідомлення: {str(e)}"
        logger.error(error_msg)
        message.reply_text(f"❌ Помилка: {error_msg}")

@restricted
def handle_direct_message(update: Update, context: CallbackContext) -> None:
    """Handler for direct (non-forwarded) messages with text or caption"""
    message = update.message
    text_content = message.text or message.caption
    if not text_content:
        message.reply_text("Немає тексту для обробки.")
        return
    
    logger.info(f"Received direct message: {text_content[:50]}...")
    
    try:
        logger.info("Sending status message to user")
        status_message = message.reply_text("Обробка вашого запиту...")
        
        logger.info("Generating rewritten text")
        rewritten_text = generate_rewrite_with_gpt(text_content)
        
        try:
            logger.info(f"Posting rewritten message to channel {TELEGRAM_CHANNEL_ID}")
            context.bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=rewritten_text,
                parse_mode=ParseMode.HTML
            )
            logger.info("Published rewritten message to channel")
            
            status_message.edit_text("✅ Повідомлення було переписано та опубліковано у каналі!")
        
        except TelegramError as telegram_error:
            error_msg = f"Помилка публікації: {str(telegram_error)}"
            logger.error(error_msg)
            status_message.edit_text(f"❌ {error_msg}")
    
    except Exception as e:
        error_msg = f"Помилка обробки повідомлення: {str(e)}"
        logger.error(error_msg)
        message.reply_text(f"❌ Помилка: {error_msg}")

def main() -> None:
    """Main function to run the bot"""
    # Check if environment variables are set
    if not all([TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, TELEGRAM_CHANNEL_ID]):
        logger.error("Required environment variables are not set. Check your .env file.")
        return
    
    # Custom request with higher timeouts
    request = Request(
        con_pool_size=8,
        connect_timeout=15.0,  # Increased from default 5.0
        read_timeout=30.0,     # Increased from default 5.0
    )
    
    try:
        # Verify bot token before starting
        logger.info("Verifying bot token...")
        test_bot = Bot(token=TELEGRAM_BOT_TOKEN, request=request)
        me = test_bot.get_me()
        logger.info(f"Bot verification successful. Connected as {me.first_name} (@{me.username})")
        
        # Create the Bot with custom request parameters
        bot = Bot(token=TELEGRAM_BOT_TOKEN, request=request)
        
        # Create the Updater with bot instance
        updater = Updater(bot=bot)
        
        # Get the dispatcher to register handlers
        dp = updater.dispatcher
        
        # Add handlers
        dp.add_handler(CommandHandler("start", start_command))
        dp.add_handler(MessageHandler(Filters.forwarded, handle_forwarded_message))
        # Include messages that have text OR captions, excluding forwarded
        dp.add_handler(MessageHandler((Filters.text | Filters.caption) & ~Filters.forwarded, handle_direct_message))
        
        # Error handler for network issues
        def error_handler(update, context):
            if isinstance(context.error, (TimedOut, NetworkError)):
                logger.error(f"Network error: {context.error}")
            else:
                logger.error(f"Error: {context.error}")
                
        dp.add_error_handler(error_handler)
        
        # Run the bot
        logger.info("Starting bot")
        updater.start_polling(timeout=60, drop_pending_updates=True)
        updater.idle()
    
    except (TimedOut, NetworkError) as network_error:
        logger.critical(f"Network error during bot startup: {network_error}")
        logger.info("Will retry in 10 seconds...")
        time.sleep(10)
        main()  # Retry 
    
    except Exception as e:
        logger.critical(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    socket.setdefaulttimeout(30)  # Increase default socket timeout
    main()