from pymongo import MongoClient
from config import DB_URL, DB_NAME

# 连接到MongoDB
client = MongoClient(DB_URL)  # 使用配置文件中的DB_URL连接到MongoDB数据库
db = client[DB_NAME]  # 选择数据库，使用配置文件中的DB_NAME

# 获取集合
exchange_codes_collection = db["exchange_codes"]  # 获取exchange_codes集合
users_collection = db["users"]  # 获取users集合
routes_collection = db["routes"]  # 获取routes集合
whitelist_collection = db['whitelist']