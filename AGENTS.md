# AGENTS.md

## Что это

Генератор `domains.lst` — списка доменов, заблокированных в РФ, по данным OONI.
Один скрипт `generate.py`, без тестов, без подпакетов.

## Окружение и запуск

- Python **3.13+** (см. `.python-version`, `pyproject.toml`).
- Менеджер пакетов — **uv**, не pip. `uv.lock` фиксирует зависимости. `requirements.txt` отсутствует — любые упоминания pip в старых Issue/PR считаются устаревшими.
- Devbox + direnv (`.envrc`, `devbox.json`) автоматически ставят окружение при `cd`.
- Запуск:
  - `uv run python3 generate.py` — напрямую.
  - `devbox run start` — то же самое через devbox-скрипт.
- По умолчанию отбираются аномалии за последние 7 дней (`days_back=7` в `main()`).

## Сетевые особенности

- Скрипт ходит на `https://api.ooni.io/api/v1/aggregation`. Сам `ooni.io` заблокирован в России — для запуска из РФ нужен VPN/прокси.
- Промежуточный `ooni_data.csv` скачивается в корень и удаляется по завершении.
- `domains.lst` — финальный артефакт, **в `.gitignore`**. Не коммитить.

## Проверки и качество

Тестов нет. Верификация изменений = линтеры.

- **Ruff** (check + format) — единственная CI-проверка (`.github/workflows/ruff.yaml`). Конфиг в `pyproject.toml` отсутствует — используются дефолты ruff.
- **pre-commit** (`.pre-commit-config.yaml`): trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict, check-added-large-files (лимит 512 КБ), markdownlint, ruff-check `--fix`, ruff-format.
- **markdownlint** (`.markdownlint.yaml`): отключён только `MD013` (длина строки).
- **Vale** (`.vale.ini`) — линтер прозы, стили `Google` и `write-good`. Каталог `styles/` **в `.gitignore`** (ставится отдельно через vale).

Перед коммитом: `pre-commit run --all-files`.

## Стиль кода

- snake_case, type hints в сигнатурах, docstring на функциях.
- Логирование — модуль `logging`, handler `StreamHandler(sys.stdout)`. Не `print`.
- Широкие `except Exception` допустимы с комментарием `# pylint: disable=broad-exception-caught` (см. `generate.py`).
- Функции возвращают `bool` — `True` = успех, `False` = неудача. Не бросают исключения наружу.
- Зависимости в `pyproject.toml` зафиксированы точными версиями (`==`). При добавлении пакета — `uv add <pkg>`.

## Структура

- `generate.py` — весь код. Точки входа: `main()`, `build_ooni_url(days_back)`, `download_file(url, file_path, timeout)`, `blocked_unique_domains(csv_path, txt_path)`.
- `.agents/skills/` — локальные skills пользователя (caveman и производные). Не трогать при правках кода.
- `styles/` — стили vale, gitignored.
- `.github/ISSUE_TEMPLATE/` — пуст.
