from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext
from config import ALLOWED_GROUP_IDS, ADMIN_ID, GROUP_INVITE_LINK
from util import delete_messages, get_now_utc
from telegram import ChatMember
from datetime import timedelta,datetime
from log import logger


async def is_user_in_allowed_group(update: Update, context: CallbackContext) -> bool:
    user_id = update.effective_user.id
    for group_id in ALLOWED_GROUP_IDS:
        try:
            chat_member = await context.bot.get_chat_member(chat_id=group_id, user_id=user_id)
            if chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER, ChatMember.RESTRICTED]:
                return True
        except Exception as e:
            logger.error(f"Error checking user in group {group_id}: {e}")
    return False
async def is_user_in_allowed_group_id(user_id: int, group_id: int, context: CallbackContext) -> bool:
    try:
        chat_member = await context.bot.get_chat_member(chat_id=group_id, user_id=user_id)
        return chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER, ChatMember.RESTRICTED]
    except Exception as e:
        logger.error(f"Error checking user in group {group_id}: {e}")
        return False
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext):
        query = update.callback_query
        user_id = update.effective_user.id
        if user_id not in ADMIN_ID:
            for group_id in ALLOWED_GROUP_IDS:
                # 禁言用户五分钟
                try:
                    now = get_now_utc()
                    await context.bot.restrict_chat_member(group_id, user_id, permissions=None, until_date=now + timedelta(minutes=5))
                except Exception as e:
                    logger.error(f"Error restricting user {user_id} in group {group_id}: {e}")
            if query is not None:
                await query.answer(text="虎奏！你是管理员嘛你就点！！！", show_alert=True, cache_time=5)
            else:
                warning_message = await update.message.reply_text("虎奏！你是管理员嘛你就发！！！")
                # 五秒后自动删除
                context.job_queue.run_once(delete_messages, 5, data={
                    'chat_id': update.effective_chat.id,
                    'user_message_id': update.message.message_id,
                    'bot_message_id': warning_message.message_id
                })
            return
        return await func(update, context)
    return wrapper

def private_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext):
        if update.effective_chat.type != 'private':
            warning_message = await update.message.reply_text("尼去私聊啊喂！！！")
            logger.warning(f"User {update.effective_user.id} tried to use {func.__name__} in a non-private chat.")

            # 五秒后自动删除
            context.job_queue.run_once(delete_messages, 5, data={
                'chat_id': update.effective_chat.id,
                'user_message_id': update.message.message_id,
                'bot_message_id': warning_message.message_id
            })
            return
        return await func(update, context)
    return wrapper

def restricted(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        chat_type = update.effective_chat.type
        if chat_type in ['group', 'supergroup']:
            # 允许群聊中的用户使用
            return await func(update, context, *args, **kwargs)
        elif chat_type == 'private':
            # 私聊中检查用户是否属于的群组
            if await is_user_in_allowed_group(update, context):
                return await func(update, context, *args, **kwargs)
            else:
                logger.info(f"User {update.effective_user.id} is not allowed to use the bot in private chat.")
                await update.message.reply_text(
                    f"抱歉，您不在群组中。\n请加入群组: [点击这里]({GROUP_INVITE_LINK})",
                    parse_mode='MarkdownV2'
                )
                return
        return await func(update, context, *args, **kwargs)
    return wrapper
