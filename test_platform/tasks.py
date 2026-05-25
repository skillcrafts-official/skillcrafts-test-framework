from celery import Celery
from django.core.files.base import ContentFile
from test_framework.test_design.test_scenarios.registry import SCENARIO_REGISTRY
# Чтобы все сценарии зарегистрировались, их нужно импортировать
import test_framework.test_design.test_scenarios.services.auth
import test_framework.test_design.test_scenarios.services.profiles


app = Celery('test_framework')
app.conf.update(
    broker_url='redis://redis_service:6379/0',
    result_backend='redis://redis_service:6379/1',   # если нужны результаты
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Moscow',
    enable_utc=True,
)

@app.task(name="app.test_framework")
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

    run.status = 'running'
    run.save()

    try:
        from test_framework.test_design.components.framework import TestProject

        if run.run_type == 'full':
            endpoints = list(SCENARIO_REGISTRY.keys())
        else:
            endpoints = run.selected_endpoints or []

        with TestProject("API Test Run", output_file=None) as project:
            for ep_key in endpoints:
                scenario_func = SCENARIO_REGISTRY.get(ep_key)
                if scenario_func:
                    scenario_func(project)

            csv_content = project.generate_csv_string()
            run.csv_file.save(f'result_{run.pk}.csv', ContentFile(csv_content))
            run.result_summary = project.get_summary()

        run.status = 'completed'
    except Exception as e:
        run.status = 'failed'
        run.result_summary = {'error': str(e)}
    finally:
        run.save()