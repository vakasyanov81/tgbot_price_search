import asyncio
import os
import time
from types import SimpleNamespace

import pytest

from autosnab_bot.handlers import priceformation as handler
from autosnab_bot.services import priceformation


def test_strip_ansi():
    assert priceformation.strip_ansi("\x1b[91m[ERROR]\x1b[0m: нет прайсов") == "[ERROR]: нет прайсов"


def test_tail_keeps_short_text():
    assert priceformation.tail("  строка 1\nстрока 2\n", 100) == "строка 1\nстрока 2"


def test_tail_cuts_by_whole_lines():
    text = "\n".join(f"line {i}" for i in range(100))
    result = priceformation.tail(text, 30)
    assert result.startswith("…\n")
    assert result.endswith("line 99")
    assert len(result) <= 32
    assert all(line.startswith("line ") for line in result.splitlines()[1:])


def test_result_files_since(monkeypatch, tmp_path):
    monkeypatch.setattr(priceformation, "RESULT_DIR", tmp_path)
    old = tmp_path / "old.xlsx"
    old.write_text("")
    os.utime(old, (time.time() - 100, time.time() - 100))
    started = time.time() - 1
    new = tmp_path / "for_drom.xlsx"
    new.write_text("")
    (tmp_path / "subdir").mkdir()

    assert priceformation.result_files_since(started) == [new]


def test_result_files_since_without_result_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(priceformation, "RESULT_DIR", tmp_path / "missing")
    assert priceformation.result_files_since(0) == []


def test_error_text_from_json():
    output = 'some log\n{"ok": false, "error": {"kind": "ValueError", "message": "нет логина"}}'
    assert handler._error_text(output) == "нет логина"


def test_error_text_falls_back_to_output():
    assert handler._error_text("Traceback\nboom") == "Traceback\nboom"
    assert handler._error_text("") == "неизвестная ошибка"


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("price.xls", True),
        ("Прайс.XLSX", True),
        ("territories.json", True),
        ("mim.zip", True),
        ("price.csv", False),
        ("xlsx", False),
        (None, False),
    ],
)
def test_is_supplier_file(file_name, expected):
    assert priceformation.is_supplier_file(file_name) is expected


def test_command_result_json_skips_uv_warnings():
    result = priceformation.CommandResult(0, 'warning: something\n{"1": {"sup_title": "Пошк"}}\n')
    assert result.json() == {"1": {"sup_title": "Пошк"}}


def test_supplier_upload_skipped_without_pending_supplier():
    context = SimpleNamespace(user_data={})
    assert asyncio.run(handler.supplier_price_upload(SimpleNamespace(), context)) is None  # type: ignore[arg-type]


def test_placed_names_from_cli_json():
    output = '{"ok": true, "files": ["/p/file_prices/mim/territories.json", "/p/file_prices/mim/price.xlsx"]}'
    result = priceformation.CommandResult(0, output)
    assert handler._placed_names(result) == ["territories.json", "price.xlsx"]


def test_placed_names_without_json():
    assert handler._placed_names(priceformation.CommandResult(0, "not json")) == []
