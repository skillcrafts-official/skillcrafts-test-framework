import os
import re
import markdown
from pathlib import Path

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, HttpResponseNotFound, Http404, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.static import serve
from django.db import transaction
from django.conf import settings
from django.utils._os import safe_join


from .models import TestRun
from .tasks import execute_tests


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


WIKI_ROOT = settings.WIKI_ROOT

def get_wiki_tree(base_path=None):
    """Рекурсивно строит дерево страниц для навигации."""
    if base_path is None:
        base_path = WIKI_ROOT
    tree = []
    try:
        entries = sorted(base_path.iterdir(), key=lambda e: (e.is_file(), e.name))
    except FileNotFoundError:
        return tree

    for entry in entries:
        if entry.name.startswith('.') or entry.name.startswith('_'):
            continue
        if entry.is_dir():
            children = get_wiki_tree(entry)
            if children:
                tree.append({
                    'name': entry.name.replace('_', ' ').title(),
                    'url_name': entry.relative_to(WIKI_ROOT).as_posix(),
                    'children': children,
                    'is_dir': True,
                })
        elif entry.suffix == '.md':
            rel = entry.relative_to(WIKI_ROOT)
            url_name = rel.with_suffix('').as_posix()
            if url_name == 'index':
                url_name = ''
            tree.append({
                'name': entry.stem.replace('_', ' ').title(),
                'url_name': url_name,
                'is_dir': False,
            })
    return tree


def wiki_page(request, page_path=''):
    """Отображает wiki-страницу по относительному пути."""
    safe_path = page_path.strip('/')
    if not safe_path:
        md_file = WIKI_ROOT / 'index.md'
        current_dir_rel = Path('')
    else:
        try:
            # Защита: не даём выйти за WIKI_ROOT
            candidate = (WIKI_ROOT / safe_path).resolve()
            if not candidate.is_relative_to(WIKI_ROOT.resolve()):
                raise Http404("No such wiki page")
            md_file = candidate.with_suffix('.md')
        except (ValueError, OSError):
            raise Http404("Invalid path")

    if not md_file.is_file():
        raise Http404("Wiki page not found")

    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Заменяем относительные пути изображений на вызов wiki_media
    # Текущая "директория" страницы для разрешения относительных ссылок
    page_dir = md_file.parent.relative_to(WIKI_ROOT).as_posix()
    if page_dir == '.':
        page_dir = ''

    def image_rewrite(match):
        alt = match.group(1)
        img_path = match.group(2)
        # Если путь уже абсолютный или внешний – не трогаем
        if img_path.startswith(('http://', 'https://', '/', 'data:')):
            return match.group(0)
        # Разрешаем относительный путь от текущей директории страницы
        if page_dir:
            media_url = f"/wiki/media/{page_dir}/{img_path}"
        else:
            media_url = f"/wiki/media/{img_path}"
        return f'![{alt}]({media_url})'

    md_content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', image_rewrite, md_content)

    # Преобразование Markdown в HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['fenced_code', 'codehilite', 'toc', 'tables']
    )

    tree = get_wiki_tree()
    current_path = safe_path if safe_path else 'index'

    context = {
        'wiki_tree': tree,
        'html_content': html_content,
        'current_path': current_path,
    }
    return render(request, 'test_platform/wiki_page.html', context)


def wiki_media(request, file_path):
    """Отдаёт медиа-файл из WIKI_ROOT по относительному пути."""
    try:
        abs_path = safe_join(WIKI_ROOT, file_path)
        # Дополнительная проверка, что остаёмся внутри WIKI_ROOT
        if not Path(abs_path).resolve().is_relative_to(WIKI_ROOT.resolve()):
            raise Http404("No such file")
        return serve(request, os.path.basename(abs_path), os.path.dirname(abs_path))
    except (ValueError, OSError):
        raise Http404("File not found")
