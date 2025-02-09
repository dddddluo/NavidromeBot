import pytz
from telegram.ext import ContextTypes
import datetime
from log import logger
import random
import string
from config import ALLOWED_GROUP_IDS


async def delete_messages(context: ContextTypes.DEFAULT_TYPE):
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


def new_exchange_code():
    # 生成一个包含8个随机大写字母和数字的兑换码
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return code


async def get_user_from_message(context: ContextTypes.DEFAULT_TYPE, message):
    if message.from_user is not None:
        member = await context.bot.get_chat_member(chat_id=ALLOWED_GROUP_IDS[0], user_id=message.from_user.id)
        return member.user
    elif message.chat is not None:
        return message.chat
    else:
        return None
async def get_user_from_id(context: ContextTypes.DEFAULT_TYPE, user_id):
    member = await context.bot.get_chat_member(chat_id=ALLOWED_GROUP_IDS[0], user_id=user_id)
    return member.user