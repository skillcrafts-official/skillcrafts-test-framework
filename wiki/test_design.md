# Процедура тест-дизайна

В общем, в данном фрейворке (skillcrafts_test_framework) сохранён канонический подход к дизайну ручных тестов (типа тест-кейсов, чек-листов, таблиц принятия решений и т.д.).

### Контекстно-ориентированный подход (ООП)

В основе написания тестов используется **протокол контекстных менеджеров**.  
На каждом уровне вложенности создаётся python-объект:  

- проект,
- тест-кейс,
- тестоый шаг.  

Это демонстрационный минимум. Если применять для боевых задач, то этот список можно бесконечно расширять.  

Например, так будет выглядеть создание проекта:
```python
@shared_task
def execute_tests(run_id):
    """
    Универсальная задача Celery для выполнения тестов.
    run_id - UUID тестового прогона из модели TestRun.
    """
    from test_platform.models import TestRun

    try:
        run = TestRun.objects.get(pk=run_id)
    except TestRun.DoesNotExist:
        return
    
    # здесь пропущены строки кода
    # ...
    
        """
        Собственно код создания проекта
        """
        with TestProject("API Test Run", output_file=None) as project:
            for ep_key in endpoints:
                scenario_func = SCENARIO_REGISTRY.get(ep_key)
                if scenario_func:
                    scenario_func(project)
    
    # и здесь опущены подробности
    # ...
```

В список `enpoints`, попадают все зарегистрированные ендпоинты схем API. Этот список формируется в импортируемой константе SCENARIO_REGISTRY.  

Таким образом, можно создавать сколько угодно сценариев и все их размещать в универсальную задачу.

Если нужно создать несколько независимых циклов с тестами, то это можно сделать за счёт расширения ендпоинтов во фреймворке django (который является движком для запуска тестов, контроля процесса выполнения и отображения результатов).

Вот как это выглядит:
```python
# views.py
def run_tests(request):
    """Запуск полного регресса."""
    run = TestRun.objects.create(run_type='full', selected_endpoints=[])
    transaction.on_commit(lambda: execute_tests.delay(str(run.pk)))
    return JsonResponse({'run_id': str(run.id)})

# urls.py
    path('run-tests/', views.run_tests, name='run_tests'),
```

Это демонстрационный минимум, сейчас все зарегистрированные тест-кейсы выполняются одним циклом.

Далее переходим непосредственно к созданию тестов внутри проекта.  

```python
@register_scenario('auth_token')
def run_auth_token_scenario(project):
    # -------------------------------------------------------
    # Тест-кейс 1: Авторизация и проверка токена
    # -------------------------------------------------------

    TEST_EMAIL = os.environ.get('email', 'user@example.com')
    TEST_PASSWORD = os.environ.get('passw', 'userUSER1!')

    auth = Auth()

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
```

В этом тесте проверяется успешность получения JWT-токенов при условном входе пользователя в тестируемый сервис.  

Таким образом создавая цепочку project.create_test_case - tc.step можно добавлять сколько угодно шагов к тест-кейсу (E2E) или unit-тесту, если шаги представляют из себя набор независимых действий пользователя.

В зависимости от выбранного интерфейса (в данном случае это REST API) можно менять и предмет тестирования (API, UI, DB и т.д.).

В итоге процесс создания тестов ничем не отличается от процесса написания ручных тест-кейсов. А в результат тестирования можно использовать для "восстановления" человеко-читаемых ручных тест-кейсов с привычними атрибута.