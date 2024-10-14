import json
import aiohttp
import logging
import random
import string
from config import API_BASE_URL, NA_ADMIN_USERNAME, NA_ADMIN_PASSWORD, LOGIN_URL

logger = logging.getLogger(__name__)

class ServiceResultType:
    SUCCESS = "success"
    ERROR = "error"

class NavidromeService:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.bearer_token = None
        self.session = None

    async def create_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def refresh_bearer_token(self):
        payload = {
            "username": NA_ADMIN_USERNAME,
            "password": NA_ADMIN_PASSWORD
        }
        headers = {
            'Content-Type': 'application/json'
        }
        logger.info(f"尝试从 {LOGIN_URL} 获取新的 Navidrome 令牌")
        await self.create_session()
        try:
            async with self.session.post(LOGIN_URL, json=payload, headers=headers) as response:
                logger.info(f"登录响应: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    self.bearer_token = data.get("token")
                    logger.info("Navidrome 令牌刷新成功。")
                    return True
                else:
                    logger.error("获取新的 Navidrome 令牌失败。")
                    return False
        except aiohttp.ClientError as e:
            logger.error(f"刷新令牌时发生错误: {e}")
            return False

    async def _make_request(self, method, endpoint, payload=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        default_headers = {
            'X-Nd-Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        headers = headers or default_headers

        await self.create_session()
        try:
            async with self.session.request(method, url, headers=headers, json=payload) as response:
                if response.status == 401:
                    logger.info("Navidrome token 已过期，正在获取新的令牌。")
                    if await self.refresh_bearer_token():
                        headers['X-Nd-Authorization'] = f'Bearer {self.bearer_token}'
                        async with self.session.request(method, url, headers=headers, json=payload) as new_response:
                            return await new_response.json(), new_response.status
                    else:
                        logger.error("刷新 Navidrome token 失败。")
                        return None, 401
                return await response.json(), response.status
        except aiohttp.ClientError as e:
            logger.error(f"请求失败: {e}")
            return None, None

    async def create_na_user(self, username, name, password):
        payload = {
            "isAdmin": False,
            "userName": username,
            "name": name,
            "password": password
        }
        return await self._make_request('POST', '/api/user', payload)

    async def delete_user(self, user_id):
        return await self._make_request('DELETE', f'/api/user/{user_id}')

    async def reset_password(self, user_id, name, username, new_password):
        payload = {
            "userName": username,
            "name": name,
            "changePassword": True,
            "password": new_password
        }
        response_data, status = await self._make_request('PUT', f'/api/user/{user_id}', payload)
        logger.info(f"{user_id}重置密码为{new_password}，结果: {response_data if response_data else 'Request failed'}, 状态码: {status}")
        if status == 200:
            return ServiceResultType.SUCCESS
        else:
            return ServiceResultType.ERROR

    async def check_token(self):
        _, status = await self._make_request('GET', '/api/translation/zh-Hans')
        return status == 200 if status is not None else False

    def generate_random_password(self, length=8):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=length))

navidrome_service = NavidromeService()
