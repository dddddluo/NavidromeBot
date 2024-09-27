# 按钮
import logging
import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import users_collection, routes_collection, whitelist_collection
from handlers.start_handler import start
from telegram.ext import ConversationHandler, CallbackContext
from telegram import Update
from config import ADMIN_ID, AWAITING_CODE, MESSAGE_HANDLER_TIMEOUT
from datetime import datetime
from util import CHINA_TZ
from bson.codec_options import CodecOptions

# 创建日志记录器
logger = logging.getLogger(__name__)

# 处理按钮点击事件的函数


async def user_info(update: Update, context: CallbackContext):
    query = update.callback_query  # 获取回调查询
    user = query.from_user  # 获取点击按钮的用户信息
    logger.info(
        f"User info requested by {user.username if user.username else 'Unknown'}.")  # 记录日志
    is_admin = user.id in ADMIN_ID

    # 查询用户是否在数据库中
    user_info = users_collection.with_options(codec_options=CodecOptions(
        tz_aware=True,
        tzinfo=CHINA_TZ)).find_one({"telegram_id": user.id})

    if user_info is None or user_info.get('user_id') is None:
        # 用户未注册，发送弹窗警告信息并返回
        await query.answer(text="虎揍先注册，再点哇！", show_alert=True, cache_time=5)
        return
    await query.answer(cache_time=5)  # 回答查询以防止超时
    last_check_in = user_info.get("last_check_in", "未知")
    username = html.escape(user_info.get("username", "无"))
    password = html.escape(user_info.get("password", "无"))
    is_whitelisted = whitelist_collection.find_one(
        {"telegram_id": user.id}) is not None
    whitelist_status = "是" if is_whitelisted else "否"

    admin_status = "是" if is_admin else "否"

    if isinstance(last_check_in, datetime):
        last_check_in = last_check_in.strftime('%Y-%m-%d %H:%M:%S')
    # 创建消息
    message = (
        f"👥虎揍信息:\n"
        f"🆔用户名: <code>{username}</code>\n"
        f"🔑密  码: <code>{password}</code>\n"
        f"💌白名单: {whitelist_status}\n"
        f"⏱️签到时间: {last_check_in}\n"
        f"🚨管理员: {admin_status}"
    )

    # 创建新的内联键盘
    keyboard = [
        [InlineKeyboardButton("🔑重置密码", callback_data='reset_password')],
        [
            InlineKeyboardButton("🔙返回", callback_data='back_to_start'),
            InlineKeyboardButton("❌️关闭", callback_data='close')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 调试日志
    logger.debug(f"Generated user info message: {message}")

    # 编辑消息以显示用户信息和新按钮
    try:
        if query.message.text:
            await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='HTML')
        elif query.message.caption:
            await query.edit_message_caption(caption=message, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        await query.message.reply_text(f"发生错误：{str(e)}", parse_mode='HTML')


async def server_info(update: Update, context: CallbackContext):
    query = update.callback_query  # 获取回调查询
    # 查询数据库中是否有此用户，并且有na账号
    user_data = users_collection.find_one({"telegram_id": query.from_user.id})
    if not user_data or user_data.get("user_id") is None:
        # 回答查询以防止超时
        await query.answer(text="虎揍没号，你点什么点！", show_alert=True, cache_time=5)
        return
    await query.answer(cache_time=5)  # 回答查询以防止超时
    logger.info("Server info requested.")
    # 获取线路信息
    routes = routes_collection.find_one({})
    if routes:
        message = "线路信息：\n" + \
            "\n".join([f"{key}: {value}" for key,
                       value in routes.items() if key != '_id'])
    else:
        message = "当前没有设置线路信息，请管理员设置。"

    # 创建新的内联键盘
    keyboard = [
        [
            InlineKeyboardButton("🔙返回", callback_data='back_to_start'),
            InlineKeyboardButton("❌️关闭", callback_data='close')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 调试日志
    logger.debug(f"Generated server info message: {message}")

    # 编辑消息以显示线路信息和新按钮
    try:
        if query.message.text:
            await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='HTML')
        elif query.message.caption:
            await query.edit_message_caption(caption=message, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        await query.message.reply_text(f"发生错误：{str(e)}", parse_mode='HTML')


async def use_code(update: Update, context: CallbackContext):
    query = update.callback_query  # 获取回调查询
    user_data = users_collection.find_one({"telegram_id": query.from_user.id})
    if user_data and user_data.get("user_id") is not None:
        # 回答查询以防止超时
        await query.answer(text="虎揍，有号了还注册！！！", show_alert=True, cache_time=5)
        return ConversationHandler.END
    await query.answer(cache_time=5)  # 回答查询以防止超时
    logger.info("Use code requested.")
    context.user_data['awaiting_code'] = True  # 确保状态设置正确
    message = (
        "🎟️【虎揍你来啦！】：\n\n"
        f"- 请在{MESSAGE_HANDLER_TIMEOUT}s内发送你的注册码，形如\n"
        "xxxx\n"
        "退出点 /cancel"
    )

    # 创建新的内联键盘
    keyboard = [
        [
            InlineKeyboardButton("🔙返回", callback_data='back_to_start'),
            InlineKeyboardButton("❌️关闭", callback_data='close')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 调试日志
    logger.debug(f"Generated use code message: {message}")

    # 编辑消息以显示使用注册码信息和新按钮
    try:
        if query.message.text:
            await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='HTML')
        elif query.message.caption:
            await query.edit_message_caption(caption=message, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        await query.message.reply_text(f"发生错误：{str(e)}", parse_mode='HTML')

    return AWAITING_CODE


async def back_to_start(update: Update, context: CallbackContext):
    try:
        await update.callback_query.answer(cache_time=5)
        await start(update, context)
    except Exception as e:
        logger.error(f"Failed to back to start: {e}")
    return ConversationHandler.END


async def close(update: Update, context: CallbackContext):
    try:
        await update.callback_query.answer(cache_time=5)
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")
    return ConversationHandler.END
