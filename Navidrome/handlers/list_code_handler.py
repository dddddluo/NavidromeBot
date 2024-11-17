import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import exchange_codes_collection
from handlers.permissions import admin_only, private_only

# 转义 MarkdownV2 特殊字符的函数


def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % escape_chars, r'\\\1', text)


@admin_only
@private_only
async def list_code(update: Update, context: CallbackContext):
    # 获取页码
    page = context.user_data.get('code_page', 1)
    items_per_page = 20
    skip = (page - 1) * items_per_page

    # 查询数据库
    all_codes_cursor = exchange_codes_collection.find(
        {"used": {"$eq": False}}).skip(skip).limit(items_per_page + 1)
    all_codes = list(all_codes_cursor)
    # 分页按钮
    page_buttons = []
    if page > 1:
        page_buttons.append(InlineKeyboardButton(
            "🔺上一页", callback_data=f'code_page_{page-1}'))
    if len(all_codes) > items_per_page:
        page_buttons.append(InlineKeyboardButton(
            "🔻下一页", callback_data=f'code_page_{page+1}'))
    if len(all_codes) == 0:
        page_buttons.append(InlineKeyboardButton(
            "🚫 暂无数据", callback_data='close'))
    keyboard = [page_buttons, [
        InlineKeyboardButton("🔙返回", callback_data='back_to_admin'),
        InlineKeyboardButton("❌ 关闭", callback_data='close')
    ]]
    if len(all_codes) > 0:
        keyboard.insert(1, [InlineKeyboardButton("🗑️ 清除所有注册码", callback_data='clear_all_codes')])
    if len(all_codes) > items_per_page:
        all_codes.pop()
    unused_codes = []
    # 将包含owner的数据排序在前面
    for code in all_codes:
        if code.get('owner'):
            used_by_link = f"[{escape_markdown_v2(str(code.get('owner')))}](tg://user?id={code.get('owner')})"
            unused_codes.append(
                f"`{escape_markdown_v2(code['code'])}` 拥有者: {used_by_link}")
        else:
            unused_codes.append(f"`{escape_markdown_v2(code['code'])}`")
    allcount = exchange_codes_collection.count_documents(
        {"used": {"$eq": False}})
    # 构建回复消息
    message = f"所有未使用的注册码总数：{allcount}\n\n"
    if unused_codes:
        message += "\n".join(unused_codes) + "\n"

    # 使用 MarkdownV2 格式回复用户
    await update.callback_query.edit_message_caption(message, parse_mode='MarkdownV2', reply_markup=InlineKeyboardMarkup(keyboard))


async def code_pagination(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer(cache_time=5)  # 快速响应回调查询

    # 从 callback_data 获取当前页码
    page = int(query.data.split('_')[-1])

    # 重新调用 list_code 函数，传入新的页码
    context.user_data['code_page'] = page
    await list_code(update, context)


@admin_only
@private_only
async def clear_all_codes(update: Update, context: CallbackContext):
    query = update.callback_query
    
    try:
        # 删除所有未使用的注册码
        result = exchange_codes_collection.delete_many({"used": {"$eq": False}})
        deleted_count = result.deleted_count
        
        # 构建回复消息
        message = f"已成功删除 {deleted_count} 个未使用的注册码\\!"
        
        # 我也会按钮了🔘乌啦啦
        keyboard = [[
            InlineKeyboardButton("🔙返回", callback_data='back_to_admin'),
            InlineKeyboardButton("❌ 关闭", callback_data='close')
        ]]
        
       
        await query.edit_message_caption(
            caption=message,
            parse_mode='MarkdownV2',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"清除注册码时发生错误: {str(e)}")
        await query.edit_message_caption(
            caption="清除注册码时发生错误\\!",
            parse_mode='MarkdownV2'
        )
