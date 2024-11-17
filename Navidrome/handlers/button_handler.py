# 按钮
import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import users_collection, routes_collection, whitelist_collection
from handlers.start_handler import start
from telegram.ext import ConversationHandler, CallbackContext
from telegram import Update
from config import ADMIN_ID, AWAITING_CODE, MESSAGE_HANDLER_TIMEOUT, config
from datetime import datetime, timezone
from util import CHINA_TZ, get_now_utc
from bson.codec_options import CodecOptions
import asyncio
from handlers.admin_menu import admin_menu
from handlers.permissions import admin_only
from log import logger


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
        await query.edit_message_caption(caption=message, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")


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
        await query.edit_message_caption(caption=message, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")


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
        await query.edit_message_caption(caption=message, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")

    return AWAITING_CODE


async def back_to_start(update: Update, context: CallbackContext):
    try:
        await asyncio.gather(update.callback_query.answer(cache_time=5), start(update, context))
    except Exception as e:
        logger.error(f"Failed to back to start: {e}")
    return ConversationHandler.END

async def back_to_admin(update: Update, context: CallbackContext):
    try:
        await asyncio.gather(update.callback_query.answer(cache_time=5), admin_menu(update, context))
    except Exception as e:
        logger.error(f"Failed to back to admin: {e}")
    return ConversationHandler.END

async def close(update: Update, context: CallbackContext):
    try:
        await asyncio.gather(update.callback_query.message.delete())
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")
    return ConversationHandler.END

async def check_in(update: Update, context: CallbackContext):
    query = update.callback_query  # 获取回调查询
    user = query.from_user  # 获取点击按钮的用户信息
    user_id = user.id
    logger.info(
        f"收到签到消息，来自用户 {user.username}（ID: {user_id})")

    user_data = users_collection.with_options(codec_options=CodecOptions(
        tz_aware=True,
        tzinfo=CHINA_TZ)).find_one({"telegram_id": user_id})
    TIME_USER_ENABLE = config.get('TIME_USER_ENABLE', True)
    if not TIME_USER_ENABLE:
        await query.answer(text="未开启签到保号，请放心使用！", show_alert=True, cache_time=5)
        return
    now = get_now_utc()
    if not user_data:
        # 如果用户不存在于数据库中，插入用户数据
        users_collection.insert_one({
            "telegram_id": user_id,
            "username": user.username,
            "last_check_in": now,
            "created_at": now
        })
        nowstr = now.astimezone(CHINA_TZ).strftime('%Y-%m-%d %H:%M:%S')
        await query.message.reply_text(f"签到成功！\n签到时间：{nowstr}")
        await query.answer(text=f"签到成功！\n签到时间：{nowstr}", show_alert=True, cache_time=5)
        logger.info(
            f"新用户 {user.username}（ID: {user_id}） 注册并签到成功。")
    else:
        today_zero = now.replace(hour=0, minute=0, second=0, microsecond=0)
        last_check_in = user_data.get('last_check_in')
        # 确保 last_check_in 是带时区的
        if last_check_in and last_check_in.tzinfo is None:
            last_check_in = last_check_in.replace(
                tzinfo=timezone.utc)
        if last_check_in is None or last_check_in < today_zero:
            # 如果用户的最后签到时间小于今天0点，则更新最后签到时间
            users_collection.update_one(
                {"telegram_id": user_id},
                {"$set": {"last_check_in": now}}
            )
            nowstr = now.astimezone(CHINA_TZ).strftime('%Y-%m-%d %H:%M:%S')
            await query.message.reply_text(f"签到成功！\n签到时间：{nowstr}")
            await query.answer(text=f"签到成功！\n签到时间：{nowstr}", show_alert=True, cache_time=5)
            logger.info(
                f"用户 {user.username}（ID: {user_id}） 签到成功。")
        else:
            await query.answer(text="虎揍！不要重复签到，再发给你关小黑屋！！", show_alert=True, cache_time=5)
            logger.info(
                f"用户 {user.username}（ID: {user_id}） 重复签到。")

@admin_only
async def admin_menu_callback(update: Update, context: CallbackContext):
    await asyncio.gather(update.callback_query.answer(cache_time=5), admin_menu(update, context))
