# В данном проекте используется пакетный менеджер uv
```
curl -LsSf https://astral.sh/uv/install.sh | sh

uv init
uv venv
sourse .venv/bin/activate
```
Далее устаналвиваются необходимые модули
```
# например
uv add requets
uv sync
```

# Запуск на локальной машине

Создать и применить миграции
```
python manage.py makemigrations
python manage.py migrate
```

Создать суперпользователя (для доступа в админку, если понадобится)
```
python manage.py createsuperuser
```

Запустить Redis (или другой брокер для Celery)
Убедись, что Redis работает на localhost:6379. Если нет – установи и запусти.
sudo apt install redis-server
redis-cli ping
redis-server

Запустить воркер Celery (в отдельном терминале)
```
celery -A skillcrafts_test_framework worker --loglevel=info
```

Запустить тестовый сервер Django
```
python manage.py runserver
```