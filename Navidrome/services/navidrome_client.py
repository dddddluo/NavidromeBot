import json
import requests
import logging
from config import API_BASE_URL, NA_ADMIN_USERNAME, NA_ADMIN_PASSWORD, LOGIN_URL

logger = logging.getLogger(__name__)

class ServiceResultType:
    SUCCESS = "success"
    ERROR = "error"

class NavidromeService:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.bearer_token = None

    def refresh_bearer_token(self):
        payload = {
            "username": NA_ADMIN_USERNAME,
            "password": NA_ADMIN_PASSWORD
        }
        headers = {
            'Content-Type': 'application/json'
        }
        logger.info(f"尝试从 {LOGIN_URL} 获取新的 Navidrome 令牌")
        response = requests.post(LOGIN_URL, json=payload, headers=headers)
        logger.info(f"登录响应: {response.status_code} - {response.text}")
        if response.status_code == 200:
            self.bearer_token = response.json().get("token")
            logger.info("Navidrome 令牌刷新成功。")
            return True
        else:
            logger.error("获取新的 Navidrome 令牌失败。")
            return False

    def _make_request(self, method, endpoint, payload=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        default_headers = {
            'X-Nd-Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        headers = headers or default_headers

        try:
            response = requests.request(method, url, headers=headers, json=payload)
            if response.status_code == 401:
                logger.info("Navidrome token 已过期，正在获取新的令牌。")
                if self.refresh_bearer_token():
                    headers['X-Nd-Authorization'] = f'Bearer {self.bearer_token}'
                    response = requests.request(method, url, headers=headers, json=payload)
                else:
                    logger.error("刷新 Navidrome token 失败。")
                    return None
            return response
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None

    def create_na_user(self, username, name, password):
        payload = {
            "isAdmin": False,
            "userName": username,
            "name": name,
            "password": password
        }
        return self._make_request('POST', '/api/user', payload)

    def delete_user(self, user_id):
        return self._make_request('DELETE', f'/api/user/{user_id}')

    def reset_password(self, user_id, name, username, new_password):
        payload = {
            "userName": username,
            "name": name,
            "changePassword": True,
            "password": new_password
        }
        response = self._make_request('PUT', f'/api/user/{user_id}', payload)
        logger.info(f"{user_id}重置密码为{new_password}，结果: {response.text if response else 'Request failed'}")
        if response and response.status_code == 200:
            return ServiceResultType.SUCCESS
        else:
            return ServiceResultType.ERROR

    def check_token(self):
        response = self._make_request('GET', '/api/translation/zh-Hans')
        return response.status_code == 200 if response else False

navidrome_service = NavidromeService()
