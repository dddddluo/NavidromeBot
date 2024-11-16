import json
import aiohttp
import logging
import random
import string
from config import API_BASE_URL, NA_ADMIN_USERNAME, NA_ADMIN_PASSWORD, LOGIN_URL

logger = logging.getLogger(__name__)

class ResponseCode:
    USERNAME_EXISTS = 5001,
    USER_NOT_FOUND = 5002,
    TOKEN_EXPIRED = 401
    SERVER_ERROR = 500
    RESET_PASSWORD_USER_NOT_FOUND = 5003
error_message = {
    ResponseCode.USERNAME_EXISTS: "虎揍换个用户名！用户名重复啦！",
    ResponseCode.TOKEN_EXPIRED: "Navidrome token 已过期，正在获取新的令牌。",
    ResponseCode.SERVER_ERROR: "服务器内部错误",
    ResponseCode.RESET_PASSWORD_USER_NOT_FOUND: "重置密码失败，用户不存在"
}
class ApiResponse:
    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data

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
                if response.status == ResponseCode.TOKEN_EXPIRED:
                    logger.info("Navidrome token 已过期，正在获取新的令牌。")
                    if await self.refresh_bearer_token():
                        headers['X-Nd-Authorization'] = f'Bearer {self.bearer_token}'
                        async with self.session.request(method, url, headers=headers, json=payload) as new_response:
                            data = await new_response.json()
                            return ApiResponse(new_response.status, "请求成功" if new_response.status == 200 else "请求失败", data)
                    else:
                        logger.error("刷新 Navidrome token 失败。")
                        return ApiResponse(ResponseCode.TOKEN_EXPIRED, "认证失败")
                data = await response.json()
                return ApiResponse(response.status, "请求成功" if response.status == 200 else "请求失败", data)
        except aiohttp.ClientError as e:
            logger.error(f"请求失败: {e}")
            return ApiResponse(500, "服务器内部错误")

    async def create_na_user(self, username, name, password):
        payload = {
            "isAdmin": False,
            "userName": username,
            "name": name,
            "password": password
        }
        response = await self._make_request('POST', '/api/user', payload)
        if response.code == 200:
            return response
        else:
            if isinstance(response.data, dict) and 'errors' in response.data:
                errors = response.data['errors']
                if 'userName' in errors and errors['userName'] == 'ra.validation.unique':
                    return ApiResponse(ResponseCode.USERNAME_EXISTS, error_message[ResponseCode.USERNAME_EXISTS], response.data)
                else:
                    return ApiResponse(ResponseCode.SERVER_ERROR, "创建用户失败，请稍后重试。")
            else:
                return ApiResponse(ResponseCode.SERVER_ERROR, "创建用户失败，请稍后重试。")

    async def delete_user(self, user_id):
        return await self._make_request('DELETE', f'/api/user/{user_id}')
    async def get_user(self, user_id):
        return await self._make_request('GET', f'/api/user/{user_id}')

    async def reset_password(self, user_id, name, username, new_password):
        response = await self.get_user(user_id)
        if response.code != 200:
            if response.code == 404:
                return ApiResponse(ResponseCode.RESET_PASSWORD_USER_NOT_FOUND, error_message[ResponseCode.RESET_PASSWORD_USER_NOT_FOUND])
            else:
                return ApiResponse(ResponseCode.SERVER_ERROR, error_message[ResponseCode.SERVER_ERROR])
        payload = {
            "userName": username,
            "name": name,
            "changePassword": True,
            "password": new_password
        }
        response = await self._make_request('PUT', f'/api/user/{user_id}', payload)
        logger.info(f"{user_id}重置密码为{new_password}，结果: {response.data if response.data else 'Request failed'}, 状态码: {response.code}")
        return response

    async def check_token(self):
        response = await self._make_request('GET', '/api/translation/zh-Hans')
        return response

    def generate_random_password(self, length=8):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=length))

navidrome_service = NavidromeService()
