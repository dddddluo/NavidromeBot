from handlers.permissions import admin_only
from database import users_collection, whitelist_collection
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Chat
from config import ALLOWED_GROUP_IDS


@admin_only
async def view_users(update, context):
    await update.callback_query.answer(cache_time=5)
    # 分页逻辑
    page = context.user_data.get('users_page', 1)
    items_per_page = 20
    skip = (page - 1) * items_per_page
    query_filter = {'user_id': {'$ne': None}, 'username': {'$ne': None}}
    users = users_collection.find(query_filter).skip(
        skip).limit(items_per_page + 1)
    users = list(users)
    # 分页按钮
    page_buttons = []
    # 分页按钮
    if page > 1:
        page_buttons.append(InlineKeyboardButton(
            "🔺上一页", callback_data=f'users_page_{page-1}'))
    if len(users) > items_per_page:
        page_buttons.append(InlineKeyboardButton(
            "🔻下一页", callback_data=f'users_page_{page+1}'))
    if len(users) == 0:
        page_buttons.append(InlineKeyboardButton(
            "🚫 暂无数据", callback_data='close'))
    keyboard = [page_buttons, [
        InlineKeyboardButton("🔙返回", callback_data='back_to_admin'),
        InlineKeyboardButton("❌ 关闭", callback_data='close')
    ]]
    if len(users) > items_per_page:
        users.pop()
    allcount = users_collection.count_documents(query_filter)
    text = f"用户总数：{allcount}\n"
    for user in users:
        text += f"TGID：<code>{user['telegram_id']}</code> - Navidrome：{user['username']}\n"
    await update.callback_query.edit_message_caption(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))


async def view_users_pagination(update, context):
    await update.callback_query.answer(cache_time=5)
    page = int(update.callback_query.data.split('_')[-1])
    context.user_data['users_page'] = page
    await view_users(update, context)


async def view_whitelist(update, context):
    await update.callback_query.answer(cache_time=5)
    # 分页
    page = context.user_data.get('whitelist_page', 1)
    items_per_page = 20
    skip = (page - 1) * items_per_page
    whitelist_users = whitelist_collection.find().skip(skip).limit(items_per_page + 1)
    whitelist_users = list(whitelist_users)
    
    # 分页按钮
    page_buttons = []
    if page > 1:
        page_buttons.append(InlineKeyboardButton(
            "🔙上一页", callback_data=f'whitelist_page_{page-1}'))
    if len(whitelist_users) > items_per_page:
        page_buttons.append(InlineKeyboardButton(
            "🔜下一页", callback_data=f'whitelist_page_{page+1}'))
    if len(whitelist_users) == 0:
        page_buttons.append(InlineKeyboardButton(
            "🚫 暂无数据", callback_data='close'))
    keyboard = [page_buttons, [
        InlineKeyboardButton("🔙返回", callback_data='back_to_admin'),
        InlineKeyboardButton("❌ 关闭", callback_data='close')
    ]]
    
    allcount = whitelist_collection.count_documents({})
    text = f"白名单总数：{allcount}\n"
    for whitelist_user in whitelist_users:
        telegram_id = whitelist_user['telegram_id']
        user = users_collection.find_one({'telegram_id': telegram_id})
        username = user['username'] if user else '未知用户名'
        text += f"TGID：<code>{telegram_id}</code> - Navidrome：{username}\n"
    
    await update.callback_query.edit_message_caption(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))


async def view_whitelist_pagination(update, context):
    await update.callback_query.answer(cache_time=5)
    page = int(update.callback_query.data.split('_')[-1])
    context.user_data['whitelist_page'] = page
    await view_whitelist(update, context)
