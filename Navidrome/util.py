import pytz
from telegram.ext import CallbackContext
import datetime
from log import logger


async def delete_messages(context: CallbackContext):
    job = context.job
    chat_id = job.data.get('chat_id')
    user_message_id = job.data.get('user_message_id')
    bot_message_id = job.data.get('bot_message_id')

    try:
        if user_message_id:
            await context.bot.delete_message(chat_id, user_message_id)
        if bot_message_id:
            await context.bot.delete_message(chat_id, bot_message_id)
        logger.info(
            f"Deleted messages {user_message_id} and {bot_message_id} from chat {chat_id}")
    except Exception as e:
        logger.error(
            f"Error deleting messages {user_message_id} and {bot_message_id} from chat {chat_id}: {e}")

# 设置中国上海时区
CHINA_TZ = pytz.timezone('Asia/Shanghai')
def get_now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


