from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, HttpResponseNotFound
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import TestRun
from .tasks import execute_tests
from django.db import transaction
from django.http import JsonResponse


@ensure_csrf_cookie
def dashboard(request):
    """Главная страница с кнопкой запуска."""
    return render(request, 'test_platform/dashboard.html')


def run_tests(request):
    """Запуск полного регресса."""
    run = TestRun.objects.create(run_type='full', selected_endpoints=[])
    transaction.on_commit(lambda: execute_tests.delay(str(run.pk)))
    return JsonResponse({'run_id': str(run.id)})


def check_run_status(request, run_id):
    run = get_object_or_404(TestRun, pk=run_id)
    data = {
        'status': run.status,
        'summary': run.result_summary,
    }
    if run.status == 'completed':
        data['csv_url'] = run.csv_file.url if run.csv_file else ''
    return JsonResponse(data)


def download_csv(request, run_id):
    run = get_object_or_404(TestRun, pk=run_id)
    if run.csv_file:
        return FileResponse(run.csv_file.open('rb'), content_type='text/csv')
    return HttpResponseNotFound("CSV файл не найден")


def get_history(request):
    """Возвращает список последних 20 запусков в формате JSON."""
    status_filter = request.GET.get('status', 'all')
    runs = TestRun.objects.order_by('-started_at')[:50]
    if status_filter != 'all':
        runs = runs.filter(status=status_filter)

    data = [{
        'id': str(run.pk),
        'status': run.status,
        'run_type': run.run_type,
        'started_at': run.started_at.isoformat() if run.started_at else '',
        'completed_at': run.completed_at.isoformat() if run.completed_at else '',
        'csv_url': run.csv_file.url if run.csv_file else '',
    } for run in runs]
    return JsonResponse(data, safe=False)
