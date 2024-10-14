import logging
import datetime
from datetime import timezone
from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import users_collection, whitelist_collection
from config import ALLOWED_GROUP_IDS, ADMIN_ID, TIME_USER, TIME_USER_ENABLE
from util import delete_messages, get_now_utc, CHINA_TZ
from handlers.permissions import admin_only
from handlers.del_user_handler import delete_user_by_telegram_id
from bson.codec_options import CodecOptions
import asyncio
# 创建日志记录器
logger = logging.getLogger(__name__)


def parse_time(time_str):
    unit = time_str[-1]
    value = int(time_str[:-1])
    if unit == 's':
        return datetime.timedelta(seconds=value)
    elif unit == 'm':
        return datetime.timedelta(minutes=value)
    elif unit == 'h':
        return datetime.timedelta(hours=value)
    elif unit == 'd':
        return datetime.timedelta(days=value)
    else:
        raise ValueError("Invalid time format")


TIME_DELTA = parse_time(TIME_USER)

# 定义签到消息处理函数


async def handle_check_in(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id

    if chat_id not in ALLOWED_GROUP_IDS:
        return

    logger.info(
        f"收到签到消息，来自用户 {update.message.from_user.username}（ID: {user_id}），群组ID: {chat_id}")

    user_data = users_collection.with_options(codec_options=CodecOptions(
        tz_aware=True,
        tzinfo=CHINA_TZ)).find_one({"telegram_id": user_id})
    if not TIME_USER_ENABLE:
        reply_message = await update.message.reply_text("未开启签到保号，请放心使用！")
        # 等待五秒后删除用户消息和bot的回复
        context.job_queue.run_once(delete_messages, 5, data={
            'chat_id': chat_id,
            'user_message_id': update.message.message_id,
            'bot_message_id': reply_message.message_id
        })
        return
    now = get_now_utc()
    if not user_data:
        # 如果用户不存在于数据库中，插入用户数据
        users_collection.insert_one({
            "telegram_id": user_id,
            "username": update.message.from_user.username,
            "last_check_in": now,
            "created_at": now
        })
        reply_message = await update.message.reply_text("签到成功！")
        # 等待五秒后删除用户消息和bot的回复
        context.job_queue.run_once(delete_messages, 5, data={
            'chat_id': chat_id,
            'user_message_id': update.message.message_id,
            'bot_message_id': reply_message.message_id
        })
        logger.info(
            f"新用户 {update.message.from_user.username}（ID: {user_id}） 注册并签到成功。")
    else:
        today_zero = now.replace(hour=0, minute=0, second=0, microsecond=0)
        last_check_in = user_data.get('last_check_in')
        print(last_check_in)
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
            reply_message = await update.message.reply_text("签到成功！")
            # 等待五秒后删除用户消息和bot的回复
            context.job_queue.run_once(delete_messages, 5, data={
                'chat_id': chat_id,
                'user_message_id': update.message.message_id,
                'bot_message_id': reply_message.message_id
            })
            logger.info(
                f"用户 {update.message.from_user.username}（ID: {user_id}） 签到成功。")
        else:
            reply_message = await update.message.reply_text("虎揍！不要重复签到，再发给你关小黑屋！！")
            # 等待五秒后删除用户消息和bot的回复
            context.job_queue.run_once(delete_messages, 5, data={
                'chat_id': chat_id,
                'user_message_id': update.message.message_id,
                'bot_message_id': reply_message.message_id
            })
            logger.info(
                f"用户 {update.message.from_user.username}（ID: {user_id}） 重复签到。")

# 定时删除未签到用户的函数


async def delete_inactive_users(context: CallbackContext):
    if TIME_USER_ENABLE:
        logger.info("Running scheduled task to delete inactive users.")

        threshold_date = get_now_utc() - TIME_DELTA
        logger.info(f"Threshold date for deletion: {threshold_date}")
        print(threshold_date)
        inactive_users = users_collection.find({
            "$or": [
                {"last_check_in": {"$lt": threshold_date}},
                {"last_check_in": None}
            ],
            "user_id": {"$ne": None},
            "whitelist": {"$ne": True}
        })
        for user in inactive_users:
            tg_id = user.get("telegram_id")
            # 检查用户ID是否为管理员或在白名单中
            if tg_id in ADMIN_ID or whitelist_collection.find_one({"telegram_id": tg_id}):
                logger.info(f"跳过管理员或白名单用户的删除。")
                continue
            # 如果有Navidrome账号，则删除Navidrome账号
            if user.get('user_id') is not None:
                code, mention, result = await delete_user_by_telegram_id(tg_id, context)
                # 发送通知消息到群里
                if code == 200:
                    notification_message = f"检测到用户 {mention} {TIME_USER}内未签到，账号已自动删除。"
                    logger.info(f"删除Navidrome用户 {mention} 成功。")
                else:
                    notification_message = f"检测到用户 {mention} {TIME_USER}内未签到，但删除账号时出错。"
                    logger.info(
                        f"删除Navidrome用户 {mention} 失败，{result}")
                for chat_id in ALLOWED_GROUP_IDS:
                    await context.bot.send_message(chat_id=chat_id, text=notification_message, parse_mode='HTML')
            # 删除用户逻辑
            users_collection.delete_one({"telegram_id": tg_id})
            logger.info(f"用户 {mention} 删除成功。")


@admin_only
async def delete_inactive_callback(update, context):
    await update.callback_query.answer(cache_time=5)
    if TIME_USER_ENABLE:
        await update.callback_query.message.reply_text("正在删除不活跃用户...")
        await delete_inactive_users(context)
        await update.callback_query.message.reply_text("执行完成！")
    else:
        await update.callback_query.message.reply_text("未开启签到保号功能！")

# 初始化调度器
scheduler = AsyncIOScheduler()


def start_scheduler(dispatcher):
    if TIME_USER_ENABLE:
        # 添加定时任务 每天0点0分0秒 执行一次
        scheduler.add_job(delete_inactive_users, 'cron', hour=0,
                          minute=0, second=0, args=[dispatcher])
        scheduler.start()


# 创建签到消息处理器
check_in_handler = MessageHandler(
    filters.TEXT & filters.Regex(r'^签到$'), handle_check_in)
