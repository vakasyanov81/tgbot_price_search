# Быстрые команды проекта: `just` — список рецептов. Повторяют CI (.github/workflows/python-app.yml)
# и .pre-commit-config.yaml; настройки берутся из pyproject.toml / setup.cfg.

# Список рецептов
help:
    @just --list

# Запустить бота
run:
    uv run python -m autosnab_bot

# Тесты с покрытием (порог 95%) — как в CI
test *ARGS:
    uv run pytest {{ARGS}}

# Быстрые тесты без покрытия
unit *ARGS:
    uv run pytest --no-cov {{ARGS}}

# Автоформат: black + ruff --fix
format:
    uv run black .
    uv run ruff check --fix .

# Стиль: black --check, ruff, flake8
lint:
    uv run black --check --diff .
    uv run ruff check .
    uv run flake8 .

# Типы и границы слоёв: mypy, import-linter
types:
    uv run mypy .
    uv run lint-imports

# Мёртвый код и безопасность: vulture, bandit, pip-audit
audit:
    uv run vulture
    uv run bandit -r autosnab_bot -c pyproject.toml
    uv run pip-audit

# Все проверки без тестов
check: lint types audit

# Полный набор перед коммитом: проверки + тесты
ci: check test
