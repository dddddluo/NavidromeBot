import bson
import os
from database import db
from config import DB_BACKUP_DIR, OWNER
import datetime
import tarfile
from util import get_now_utc
from handlers.permissions import admin_only
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
from config import config_path, DB_BACKUP_RETENTION_DAYS


async def backup_db_job(context):
    await context.bot.send_message(chat_id=OWNER, text="备份数据库ing")
    collections = db.list_collection_names()
    if not os.path.exists(DB_BACKUP_DIR):
        os.makedirs(DB_BACKUP_DIR)
    # 获取当前时间
    now = datetime.datetime.now()
    # 保留期限设置为7天
    retention_period = datetime.timedelta(days=DB_BACKUP_RETENTION_DAYS)

    # 遍历备份目录中的所有文件
    for filename in os.listdir(DB_BACKUP_DIR):
        if 'mongo_backup' in filename and filename.endswith('.tar.gz'):
            # 解析文件中的日期
            file_date_str = filename.split('_')[-1].replace('.tar.gz', '')
            file_date = datetime.datetime.strptime(file_date_str, '%Y%m%d')
            # 如果文件日期加上保留期限仍早于当前日期，则删除该文件
            if now - file_date > retention_period:
                file_path = os.path.join(DB_BACKUP_DIR, filename)
                os.remove(file_path)
        if 'config_' in filename and filename.endswith('.json'):
            # 解析文件中的日期
            file_date_str = filename.split('_')[-1].replace('.json', '')
            file_date = datetime.datetime.strptime(file_date_str, '%Y%m%d')
            # 如果文件日期加上保留期限仍早于当前日期，则删除该文件
            if now - file_date > retention_period:
                file_path = os.path.join(DB_BACKUP_DIR, filename)
                os.remove(file_path)
    tar_file = dump_db(collections, db, DB_BACKUP_DIR)
    dump_config_file = dump_config_json(config_path, os.path.join(DB_BACKUP_DIR, f'config_{now.strftime("%Y%m%d")}.json'))
    if dump_config_file:
        await context.bot.send_document(chat_id=OWNER, document=dump_config_file)
    await context.bot.send_document(chat_id=OWNER, document=tar_file)
    await context.bot.send_message(chat_id=OWNER, text=f"备份配置文件完成\n文件名：`{dump_config_file}`\n备份数据库完成\n文件名：`{tar_file}`", parse_mode="MarkdownV2")

@admin_only
async def backup_db(update, context):
    try:
        await update.effective_message.delete()
    except:
        pass
    await backup_db_job(context)


def dump_db(collections, db, path):
    """
    MongoDB Dump

    :param collections: Database collections name
    :param db: client[db]
    :param path:
    :return:

    >>> DB_BACKUP_DIR = './backups'
    >>> conn = MongoClient("mongodb://admin:admin@127.0.0.1:27017", authSource="admin")
    >>> db_name = 'my_db'
    >>> collections = ['collection_name', 'collection_name1', 'collection_name2']
    >>> dump(collections, conn, db_name, DB_BACKUP_DIR)
    """
    now = get_now_utc()
    for coll in collections:
        with open(os.path.join(path, f'{coll}.bson'), 'wb+') as f:
            for doc in db[coll].find():
                f.write(bson.BSON.encode(doc))
    # 打包成压缩包
    tar = tarfile.open(os.path.join(
        path, f'mongo_backup_{now.strftime("%Y%m%d")}.tar.gz'), mode="w:gz")
    for coll in collections:
        tar.add(os.path.join(path, f'{coll}.bson'))
    tar.close()
    return os.path.join(path, f'mongo_backup_{now.strftime("%Y%m%d")}.tar.gz')
def dump_config_json(sourcepath, destpath):
    if os.path.exists(sourcepath):
        with open(sourcepath, 'r') as config_file:
            config_data = json.load(config_file)
            with open(destpath, 'w') as dest_file:
                json.dump(config_data, dest_file, indent=4)
                return destpath
    return None
def restore(path, db):
    """
    MongoDB Restore

    :param path: Database dumped path
    :param conn: MongoDB client connection
    :param db_name: Database name
    :return:

    >>> DB_BACKUP_DIR = '/path/backups/'
    >>> conn = MongoClient("mongodb://admin:admin@127.0.0.1:27017", authSource="admin")
    >>> db_name = 'my_db'
    >>> restore(DB_BACKUP_DIR, conn, db_name)

    """

    for coll in os.listdir(path):
        if coll.endswith('.bson'):
            with open(os.path.join(path, coll), 'rb+') as f:
                db[coll.split('.')[0]].insert_many(bson.decode_all(f.read()))
# 初始化调度器
scheduler = AsyncIOScheduler()


def backup_db_scheduler(dispatcher):
    scheduler.add_job(backup_db_job, 'cron', hour=4,
                      minute=0, second=0, args=[dispatcher])
    scheduler.start()
