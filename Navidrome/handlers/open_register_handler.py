import asyncio
import logging
from util import get_now_utc

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackContext
from config import AWAITING_OPEN_REGISTER_USERNAME, AWAITING_OPEN_REGISTER_SLOTS, ALLOWED_GROUP_IDS, TELEGRAM_BOT_NAME, MESSAGE_HANDLER_TIMEOUT, START_PIC
from database import users_collection
from handlers.create_handler import create_na_user, generate_random_password
from handlers.permissions import admin_only
# 注册队列

logger = logging.getLogger(__name__)

registration_queue = asyncio.Queue()


async def set_open_reg_slots(num_slots):
    if int(num_slots) == 0:
        await clear_queue(registration_queue)
    for _ in range(int(num_slots)):
        await registration_queue.put(True)
    return int(num_slots)


async def clear_queue(queue):
    while not queue.empty():
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            return


@admin_only
async def close_register_admin_callback(update, context):
    if registration_queue.empty():
        await update.callback_query.answer(text="虎揍没开放注册呢！", show_alert=True, cache_time=5)
        return
    await update.callback_query.answer(cache_time=5)
    if 'open_register_message_id' in context.bot_data:
        for group_id in ALLOWED_GROUP_IDS:
            try:
                await context.bot.delete_message(chat_id=group_id, message_id=context.bot_data['open_register_message_id'])
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
            await context.bot.send_photo(chat_id=group_id, photo=START_PIC, caption="虎揍别点了，等下次开放！！")
        context.bot_data.pop('open_register_message_id', None)
        await clear_queue(registration_queue)
        await update.effective_chat.send_message("关闭注册成功")


@admin_only
async def open_register_admin_callback(update, context):
    await update.callback_query.answer(cache_time = 5)
    await update.effective_chat.send_message(f"请在{MESSAGE_HANDLER_TIMEOUT}s内发送开放注册的名额数量, 退出点 /cancel")
    return AWAITING_OPEN_REGISTER_SLOTS


async def open_register_admin_num_handler(update, context):
    try:
        num_slots = int(update.effective_message.text)
    except ValueError:
        await update.effective_chat.send_message("这好像不是一个数字，请重新发送，退出点 /cancel")
        return AWAITING_OPEN_REGISTER_SLOTS
    await set_open_reg_slots(num_slots)
    await update.effective_chat.send_message(f"开放注册成功, 当前开放注册名额{num_slots}个")
    for group_id in ALLOWED_GROUP_IDS:
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "冲冲冲！！！", url=f"https://t.me/{TELEGRAM_BOT_NAME}")
        ]])
        open_register_message = await context.bot.send_photo(chat_id=group_id, photo=START_PIC, caption=f"虎揍快来\n当前开放注册名额{num_slots}个", reply_markup=reply_markup)
        context.bot_data['open_register_message_id'] = open_register_message.message_id
    return ConversationHandler.END


async def open_register_user_callback(update: Update, context: CallbackContext):
    query = update.callback_query  # 获取回调查询
    user = query.from_user  # 获取点击按钮的用户信息
    if users_collection.find_one({"telegram_id": user.id, "user_id": {"$ne": None}}):
        # 回答查询以防止超时
        await query.answer(text="虎揍，有号了还注册！！！", show_alert=True, cache_time=5)
        return ConversationHandler.END
    if registration_queue.empty():
        # 回答查询以防止超时
        await query.answer(text="虎揍！当前未开放，请等待。", show_alert=True, cache_time=5)
        return ConversationHandler.END
    # 回答查询以防止超时
    await query.answer(text="免除虎揍注册码要求，开注啦。", show_alert=True, cache_time=5)
    keyboard = [
        [
            InlineKeyboardButton("🔙返回", callback_data='back_to_start'),
            InlineKeyboardButton("❌️关闭", callback_data='close')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_caption(caption=f"请在{MESSAGE_HANDLER_TIMEOUT}s内输入你的Navidrome账号名，退出点 /cancel", reply_markup=reply_markup)
    return AWAITING_OPEN_REGISTER_USERNAME


async def open_register_user_handler(update: Update, context: CallbackContext):
    mess = update.message.text
    try:
        tgid = update.message.from_user.id
        registration_queue.get_nowait()
        username = mess
        name = mess
        password = generate_random_password()
        response = await create_na_user(username, name, password, context)
        if response is not None and response.status_code == 200:
            logger.info(f"User {username} created successfully.")  # 调试日志
            nauser_data = response.json()
            user_id = nauser_data.get("id")  # 获取用户ID
            if users_collection.find_one({"telegram_id": tgid}):
                users_collection.update_one(
                    {"telegram_id": tgid},
                    {"$set": {
                        "username": username,
                        "name": name,
                        "password": password,
                        "user_id": user_id,
                    }}
                )
            else:
                users_collection.insert_one({
                    "telegram_id": tgid,
                    "username": username,
                    "name": name,
                    "password": password,
                    "user_id": user_id,  # 保存用户ID
                    "created_at": get_now_utc(),  # 添加创建时间
                    "last_check_in": None  # 添加最后签到时间，初始为None
                })
            await update.message.reply_text(
                f"恭喜你，账号创建成功。\n用户名: `{username}`\n密码: `{password}`\n用户ID: `{user_id}`",
                parse_mode='MarkdownV2'
            )
            context.user_data.clear()
        else:
            logger.error(
                f"Failed to create user: {response.text if response else 'Unknown error'}")  # 调试日志
            if "ra.validation.unique" in response.text:
                await update.message.reply_text("用户名已存在，请重新输入。")
                return AWAITING_OPEN_REGISTER_USERNAME
            else:
                await update.message.reply_text("创建用户失败")
            context.user_data.clear()
    except asyncio.QueueEmpty:
        await update.message.reply_text("虎揍名额满啦！！")
    except Exception as e:
        await update.message.reply_text(f"创建用户失败，请重试。\n{e}")
    return ConversationHandler.END
