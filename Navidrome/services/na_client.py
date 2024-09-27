import json
import requests
from config import API_BASE_URL, NA_ADMIN_USERNAME, NA_ADMIN_PASSWORD
from token_manager import get_bearer_token
import logging
from database import users_collection
from token_manager import refresh_bearer_token

logger = logging.getLogger(__name__)
class ServiceResultType:
    SUCCESS = "success"
    ERROR = "error"

class NavidromeService:
    def __init__(self):
        self.base_url = API_BASE_URL

    async def create_na_user(self, username, name, password):
        url = f"{self.base_url}/api/user"

        payload = {
            "isAdmin": False,
            "userName": username,
            "name": name,
            "password": password
        }
        json_payload = json.dumps(payload)

        headers = {
            'X-Nd-Authorization': f'bearer {get_bearer_token()}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=json_payload)
        if response is not None and response.status_code == 401:
            logger.info("Navidrome token 已过期，正在获取新的令牌。")
            if refresh_bearer_token():
                headers['X-Nd-Authorization'] = f'bearer {get_bearer_token()}'
                response = requests.post(
                    url, headers=headers, data=json_payload)
            else:
                logger.error("刷新 Navidrome token 失败。")
                return None

        return response

    def delete_user_by_telegram_id(self, user_id):

        logger.debug(f"user_data: {user_data}")  # 添加调试日志
        user_id = user_data.get("user_id")  # 使用 .get() 方法避免 KeyError
        if not user_id:
            return "Navidrome中未找到此用户。"

        url = f"{API_BASE_URL}/api/user/{user_id}"

        headers = {
            'X-Nd-Authorization': f'Bearer {get_bearer_token()}',
            'Content-Type': 'application/json'
        }

        response = requests.delete(url, headers=headers)

        # 如果未认证，尝试刷新令牌并重试请求
        if response.status_code == 401:  # 未认证
            logger.info("Token 已过期，正在获取新的令牌。")
            if refresh_bearer_token():
                headers['X-Nd-Authorization'] = f'Bearer {get_bearer_token()}'
                response = requests.delete(url, headers=headers)
                if response.status_code == 200:
                    users_collection.delete_one({"telegram_id": telegram_id})
                    return f"用户 {user_data['username']} 删除成功。"
                else:
                    return f"删除用户失败：{response.text}"
            else:
                return "删除用户失败：无法刷新令牌。"

        if response.status_code == 200:
            # todo 不要牵扯到数据库逻辑，改到外面业务层处理, 只返回Navidrome删除用户的结果
            # 从数据库中删除用户记录
            users_collection.delete_one({"telegram_id": telegram_id})
            return f"用户 {user_data['username']} 删除成功。"
        else:
            return f"删除用户失败：{response.text}"

    def reset_password(self, user_id, name, username,  new_password):
        url = f"{self.base_url}/api/user/{user_id}"
        payload = {
            "userName": username,
            "name": name,
            "changePassword": True,
            "password": new_password
        }
        headers = {
            'X-Nd-Authorization': f'Bearer {get_bearer_token()}',
            'Content-Type': 'application/json'
        }
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code == 401:
            logger.info("Token 已过期，正在获取新的令牌。")
            if refresh_bearer_token():
                headers['X-Nd-Authorization'] = f'Bearer {get_bearer_token()}'
                response = requests.put(url, headers=headers, json=payload)
        logger.info(f"{user_id}重置密码为{new_password}，结果: {response.text}")
        if response is not None and response.status_code == 200:
            return ServiceResultType.SUCCESS
        else:
            return ServiceResultType.ERROR


navidrome_service = NavidromeService()
