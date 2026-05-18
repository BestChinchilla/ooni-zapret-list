# AGENTS.md

## Language

- Отвечать на русском, если пользователь явно не запросил другой язык.

## Проект

Единственный скрипт — `generate.py`. Скачивает CSV с OONI API, фильтрует заблокированные домены, записывает результат в `domains.lst`.

- `domains.lst` — генерируемый артефакт (в `.gitignore`), не редактировать вручную.
- `requirements.txt` — закреплённые версии включая транзитивные зависимости.

## Команды

```bash
# Запуск генерации
pip install -r requirements.txt
python3 ./generate.py

# Линтинг (то, что делает CI)
pip install -r requirements.txt
pylint $(git ls-files '*.py')
```

## Окружение

- Python 3.13.
- Dev-окружение: devbox + direnv (`.envrc` / `devbox.json`). При входе в директорию автоматически создаётся venv и ставятся зависимости.
- Скрипт обращается к `api.ooni.io` — требуется сеть; домен `ooni.io` может быть заблокирован.

## Lint и форматирование

- CI: только `pylint` (`.github/workflows/pylint.yml`).
- Markdown: `markdownlint` (MD013 отключена), `vale` со стилями Google + write-good.
- Нет `pyproject.toml`, `ruff`, `mypy`, `pytest` — не ссылаться на то, чего нет.

## Тесты

При изменении логики — проверять ручным запуском `python3 ./generate.py`.
Затем запускать `pylint $(git ls-files '*.py')` и исправлять все найденные ошибки
