import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from config import config, update_config
from handlers.permissions import admin_only

logger = logging.getLogger(__name__)

@admin_only
async def task_control_menu(update: Update, context: CallbackContext):
    """显示任务控制菜单"""
    query = update.callback_query
    await query.answer()
    BACKUP_DB_ENABLE = config.get('BACKUP_DB_ENABLE', True)
    TIME_USER_ENABLE = config.get('TIME_USER_ENABLE', True)
    # 根据当前状态设置按钮文本
    backup_status = "✅" if BACKUP_DB_ENABLE else "❌"
    time_user_status = "✅" if TIME_USER_ENABLE else "❌"

    keyboard = [
        [InlineKeyboardButton(f"数据库自动备份 {backup_status}", callback_data="toggle_backup")],
        [InlineKeyboardButton(f"自动删除不活跃用户 {time_user_status}", callback_data="toggle_time_user")],
        [InlineKeyboardButton("返回", callback_data="admin_menu")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_caption(
        caption="任务控制面板\n\n"
             f"数据库自动备份: {'开启' if BACKUP_DB_ENABLE else '关闭'}\n"
             f"自动删除不活跃用户: {'开启' if TIME_USER_ENABLE else '关闭'}",
        reply_markup=reply_markup
    )

@admin_only
async def toggle_backup(update: Update, context: CallbackContext):
    """切换数据库自动备份状态"""
    query = update.callback_query
    await query.answer()
    BACKUP_DB_ENABLE = config.get('BACKUP_DB_ENABLE', True)
    BACKUP_DB_ENABLE =  not BACKUP_DB_ENABLE
    print(BACKUP_DB_ENABLE)
    # 更新配置文件
    update_config('BACKUP_DB_ENABLE', BACKUP_DB_ENABLE)

    # 返回任务控制菜单
    await task_control_menu(update, context)

@admin_only
async def toggle_time_user(update: Update, context: CallbackContext):
    """切换自动删除不活跃用户状态"""
    query = update.callback_query
    await query.answer()
    
    TIME_USER_ENABLE = config.get('TIME_USER_ENABLE', True)
    TIME_USER_ENABLE = not TIME_USER_ENABLE
    
    # 更新配置文件
    update_config('TIME_USER_ENABLE', TIME_USER_ENABLE)
    
    # 返回任务控制菜单
    await task_control_menu(update, context)
