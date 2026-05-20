from ..registry import register_scenario
from test_framework.test_models.api.skillcrafts import Auth


@register_scenario('auth_token')
def run_auth_token_scenario(project):
    # -------------------------------------------------------
    # Тест-кейс 1: Авторизация и проверка токена
    # -------------------------------------------------------

    TEST_EMAIL = "user@example.com"
    TEST_PASSWORD = "userUSER1!"

    # Создаем экземпляр Auth для тестового пользователя.
    auth = Auth()
    # Создаём фабрику профилей для авторизованного пользователя.
    # profiles_factory = ProfileFactory().generate_profiles(5)
    # print(profiles_factory)

    with project.create_test_case(
        title="User Authentication Flow",
        priority="Critical",
        tags=["smoke", "auth"]
    ) as tc:

        with tc.step("Получить токен по email и паролю",
                     "Успешный ответ с access и refresh токенами"):
            tokens = auth.token(TEST_EMAIL, TEST_PASSWORD)
            auth.assert_status_code(200)
            auth.assert_json_has_key("access")
            auth.assert_json_has_key("refresh")

        with tc.step("Проверить, что токен доступа валиден",
                     "Метод token_verify возвращает True"):
            is_valid = auth.token_verify()
            assert is_valid, "Токен доступа не прошел проверку"

        with tc.step("Обновить токен доступа по refresh-токену",
                     "Успешный ответ с новым access-токеном"):
            new_tokens = auth.token_refresh()
            auth.assert_status_code(200)
            assert new_tokens.get("access") != tokens.get("access"), "Токен доступа не изменился после обновления"
