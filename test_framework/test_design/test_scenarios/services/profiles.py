from ..registry import register_scenario
from test_framework.test_models.api.skillcrafts import ProfilesService
from test_framework.data_factories.profiles_factory import ProfileFactory


@register_scenario('profiles')
def run_profiles_scenario(project):
    # -------------------------------------------------------
    # Тест-кейс 2: Получение профиля (требует авторизацию)
    # -------------------------------------------------------

    # Создаём фабрику профилей для авторизованного пользователя.
    profiles_factory = ProfileFactory().generate_profiles(5)
    print(profiles_factory)

    with project.create_test_case(
        title="Get User Profile",
        priority="High",
        tags=["smoke", "profiles"]
    ) as tc:
        # ProfilesService унаследован от Auth и будет использовать тот же экземпляр-синглтон
        profiles = ProfilesService()

        # Убедимся, что токен все еще действителен, если нет - обновим
        if not profiles.token_verify():
            profiles.token_refresh()

        with tc.step("Получить список всех профилей",
                     "Ответ 200, список не пуст"):
            all_profiles = profiles.get_profiles()
            profiles.assert_status_code(200)
            assert len(all_profiles) > 0, "Список профилей пуст"

        with tc.step("Получить профиль авторизованного пользователя",
                     "Ответ 200, профиль содержит пользователя"):
            my_profile = profiles.get_profile()
            profiles.assert_status_code(200)
            # profiles.assert_json_value("email", TEST_EMAIL)

        with tc.step("Получить профиль любого пользователя",
                     "Ответ 200, профиль содержит пользователя"):
            my_profile = profiles.get_profile(user_id=24)
            profiles.assert_status_code(200)

        with tc.step("Изменить профиль авторизованного пользователя",
                     "Ответ 200, профиль содержит email пользователя"):
            my_profile = profiles.edit_profile(data=profiles_factory[0])
            profiles.assert_status_code(200)
            # profiles.assert_json_value("email", TEST_EMAIL)

        with tc.step("Удалить профиль авторизованного пользователя",
                     "Ответ 201, профиль пользователя мягко удалён (обнулены данные)"):
            my_profile = profiles.get_profile()
            profiles.assert_status_code(201)
            # profiles.assert_json_value("email", TEST_EMAIL)

        with tc.step("Изменить профиль любого пользователя",
                     "Ответ 403, нельзя изменить профиль неавторизованного пользователя"):
            my_profile = profiles.edit_profile(user_id=24, data=profiles_factory[0])
            profiles.assert_status_code(403)
            # profiles.assert_json_value("email", TEST_EMAIL)

        with tc.step("Удалить профиль любого пользователя",
                     "Ответ 403, нельзя удалить профиль неавторизованного пользователя"):
            my_profile = profiles.remove_profile(user_id=24)
            profiles.assert_status_code(403)
            # profiles.assert_json_value("email", TEST_EMAIL)
