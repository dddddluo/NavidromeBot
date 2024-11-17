from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
from util import get_now_utc
from telegram import BotCommand
from telegram import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeChat, BotCommandScopeChatMember
import asyncio
from config import ADMIN_ID, ALLOWED_GROUP_IDS
from log import logger


async def set_bot_command(context):
    logger.info("set bot command job start")
    default_private_commands = [BotCommand('start', '开启主面板'),
                                ]
    default_group_commands = []
    admin_private_commands = default_private_commands + [
        BotCommand('help', '查看帮助信息'),
        BotCommand('new_code', '创建新的兑换码'),
        BotCommand('del_user', '回复消息或tgid删除Navirome账号'),
        BotCommand('new_line', '新增或修改线路'),
        BotCommand('del_line', '删除线路'),
        BotCommand('add_whitelist', '回复消息或tgid添加白名单'),
        BotCommand('del_whitelist', '回复消息或tgid删除白名单'),
        BotCommand('delete_inactive', '删除非活跃用户'),
        BotCommand('na_token', '手动刷新Navirome Token'),
    ]
    admin_group_commands = [BotCommand('new_code', '创建新的兑换码'),
                            BotCommand('del_user', '回复消息删除用户'),
                            BotCommand('add_whitelist', '回复消息添加白名单'),
                            BotCommand('del_whitelist', '回复消息删除白名单'),
                            BotCommand('delete_inactive', '删除非活跃用户'),
                            ]
    await asyncio.gather(context.bot.delete_my_commands(scope=BotCommandScopeAllGroupChats()),  # 删除所有群聊指令
                         context.bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats()))  # 删除所有私聊命令
    await asyncio.gather(context.bot.set_my_commands(default_private_commands, scope=BotCommandScopeAllPrivateChats()),  # 所有私聊命令
                         context.bot.set_my_commands(default_group_commands, scope=BotCommandScopeAllGroupChats()))  # 所有群聊命令
    for admin in ADMIN_ID:
        try:
            # 私聊
            await context.bot.set_my_commands(admin_private_commands, scope=BotCommandScopeChat(chat_id=admin))
        except Exception as e:
            logger.warning('set admin private bot command error! %s', e)
            pass
        try:
            for group in ALLOWED_GROUP_IDS:
                # 群组
                await context.bot.set_my_commands(admin_group_commands,
                                                  scope=BotCommandScopeChatMember(chat_id=group, user_id=admin))
        except Exception as e:
            logger.warning('set admin group bot command error! %s', e)
            pass
    logger.info("set bot command job end")
# 初始化调度器
scheduler = AsyncIOScheduler()


def set_bot_command_scheduler(dispatcher):
    now = get_now_utc()
    scheduler.add_job(set_bot_command, 'date', run_date=now +
                      datetime.timedelta(seconds=10), args=[dispatcher])
    scheduler.start()
