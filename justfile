# Быстрые команды проекта: `just` — список рецептов. Повторяют CI (.github/workflows/python-app.yml)
# и .pre-commit-config.yaml; настройки берутся из pyproject.toml / setup.cfg.

# Список рецептов
help:
    @just --list

# Запустить бота
run:
    uv run python -m autosnab_bot

# Запустить бота в фоне (PID в bot.pid, лог в bot.log)
start:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f bot.pid ] && kill -0 "$(cat bot.pid)" 2>/dev/null; then
        echo "Бот уже запущен (PID $(cat bot.pid))"; exit 0
    fi
    nohup setsid uv run python -m autosnab_bot >> bot.log 2>&1 &
    echo $! > bot.pid
    echo "Бот запущен (PID $(cat bot.pid)), лог: bot.log"

# Остановить фонового бота
stop:
    #!/usr/bin/env bash
    if [ -f bot.pid ] && kill -0 "$(cat bot.pid)" 2>/dev/null; then
        pkill -TERM -P "$(cat bot.pid)" || true
        kill "$(cat bot.pid)" || true
        echo "Бот остановлен"
    else
        echo "Бот не запущен"
    fi
    rm -f bot.pid

# Перезапустить фонового бота
restart: stop start

# Состояние фонового бота
status:
    #!/usr/bin/env bash
    if [ -f bot.pid ] && kill -0 "$(cat bot.pid)" 2>/dev/null; then
        echo "Бот работает (PID $(cat bot.pid))"
    else
        echo "Бот не запущен"
    fi

# Хвост лога фонового бота
logs:
    tail -f bot.log

# Установить и запустить systemd-сервис (автоперезапуск при падении, автозапуск при старте системы)
service-install:
    #!/usr/bin/env bash
    set -euo pipefail
    unit="$HOME/.config/systemd/user/autosnab-bot.service"
    mkdir -p "$(dirname "$unit")"
    sed -e "s|@WORKDIR@|$PWD|" -e "s|@UV@|$(command -v uv)|" deploy/autosnab-bot.service > "$unit"
    systemctl --user daemon-reload
    systemctl --user enable --now autosnab-bot.service
    echo "Сервис установлен. Чтобы он работал без входа в систему и стартовал при загрузке: sudo loginctl enable-linger $USER"

# Удалить systemd-сервис
service-uninstall:
    #!/usr/bin/env bash
    systemctl --user disable --now autosnab-bot.service || true
    rm -f "$HOME/.config/systemd/user/autosnab-bot.service"
    systemctl --user daemon-reload

# Состояние systemd-сервиса
service-status:
    systemctl --user status autosnab-bot.service --no-pager

# Перезапустить systemd-сервис (после обновления кода)
service-restart:
    systemctl --user restart autosnab-bot.service

# Лог systemd-сервиса (journalctl -f)
service-logs:
    journalctl --user -u autosnab-bot.service -f

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
