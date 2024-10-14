from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers.permissions import admin_only


@admin_only
async def admin_menu(update, context):
    keyboard = [
        [
            InlineKeyboardButton("👥查看用户", callback_data='view_users'),
            InlineKeyboardButton("🎖查看白名单", callback_data='view_whitelist'),
        ],
        [
            InlineKeyboardButton("🔄删除不活跃用户", callback_data='delete_inactive'),
            InlineKeyboardButton("🔖查看注册码", callback_data='list_code'),
        ],
        [
            InlineKeyboardButton("📚备份数据库", callback_data='backup_db'),
            InlineKeyboardButton("✅开放注册", callback_data='open_register_admin'),
            InlineKeyboardButton("❎关闭注册", callback_data='close_register_admin'),
        ],
        [
            InlineKeyboardButton("🔙返回", callback_data='back_to_start'),
            InlineKeyboardButton("❌️关闭", callback_data='close')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_caption(caption="欢迎进入管理面板，请选择功能👇", reply_markup=reply_markup, parse_mode='HTML')
