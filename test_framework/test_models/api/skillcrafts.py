# api_services.py
import requests
from typing import Optional, Any
from test_framework.test_models.api.base import BaseService

from test_framework.test_factories.api.base_mixins import ApiBaseAssertsMixin


class Auth(BaseService, ApiBaseAssertsMixin):
    # Общие токены для всех экземпляров и всех наследников
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id = str | None

    def __init__(self, base_url: str = None):
        super().__init__()
        if base_url:
            self.BASE_URL = base_url

    def _get_headers(self) -> dict:
        headers = super()._get_headers()
        if Auth.access_token:
            headers["Authorization"] = f"Bearer {Auth.access_token}"
        return headers

    def token(self, email: str, password: str) -> dict:
        """Получает access + refresh токены."""
        self.post("/auth/token/", data={"email": email, "password": password})
        self.assert_status_code(200)
        tokens = self.last_response.json()
        Auth.access_token = tokens.get("access")
        Auth.refresh_token = tokens.get("refresh")
        Auth.user_id = tokens.get("user_id")
        return tokens

    def token_refresh(self) -> dict:
        """Обновляет access-токен по refresh-токену."""
        if not Auth.refresh_token:
            # raise ValueError("Refresh-токен не установлен. Сначала выполните вход.")
            return False
        self.post("/auth/token/refresh/", data={"refresh": Auth.refresh_token})
        self.assert_status_code(200)
        tokens = self.last_response.json()
        Auth.access_token = tokens.get("access")
        if "refresh" in tokens:
            Auth.refresh_token = tokens["refresh"]
        return tokens

    def token_verify(self) -> bool:
        """Проверяет, что текущий access-токен действителен."""
        if not Auth.access_token:
            # raise ValueError("Access-токен не установлен.")
            return False
        self.post("/auth/token/verify/", data={"token": Auth.access_token})
        return self.last_response.status_code == 200


class ProfilesService(Auth):
    def get_profiles(self) -> list:
        self.get(path="/profiles/")
        if self.last_response.status_code in {500, }:
            return {
                "status_code": self.last_response.status_code
            }
        return self.last_response.json()

    def get_profile(self, user_id: int | None = None) -> dict:
        if not user_id:
            user_id = self.user_id
        self.get(path=f"/profiles/{user_id}/")
        if self.last_response.status_code in {500, }:
            return {
                "status_code": self.last_response.status_code
            }
        return self.last_response.json()
    
    def edit_profile(self, user_id: int | None = None, data: dict | None = None) -> dict:
        if not user_id:
            user_id = self.user_id
        self.post(path=f"/profiles/{user_id}/", data=data)
        if self.last_response.status_code in {500, }:
            return {
                "status_code": self.last_response.status_code
            }
        return self.last_response.json()
    
    def remove_profile(self, user_id: int | None = None) -> dict:
        if not user_id:
            user_id = self.user_id
        self.delete(path=f"/profiles/{user_id}/")
        if self.last_response.status_code in {500, }:
            return {
                "status_code": self.last_response.status_code
            }
        return self.last_response.json()
