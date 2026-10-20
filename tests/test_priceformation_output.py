from autosnab_bot.services.priceformation_cli import CommandResult
from autosnab_bot.services.priceformation_output import error_text, log_block, placed_names, update_report


def test_error_text_from_json() -> None:
    output = 'some log\n{"ok": false, "error": {"kind": "ValueError", "message": "нет логина"}}'
    assert error_text(output) == 'нет логина'


def test_error_text_kind_when_no_message() -> None:
    assert error_text('{"ok": false, "error": {"kind": "ValueError"}}') == 'ValueError'


def test_error_text_falls_back_to_output() -> None:
    assert error_text('Traceback\nboom') == 'Traceback\nboom'
    assert error_text('[1, 2]') == '[1, 2]'
    assert error_text('') == 'неизвестная ошибка'


def test_placed_names() -> None:
    output = '{"ok": true, "files": ["/p/file_prices/mim/territories.json", "/p/file_prices/mim/price.xlsx"]}'
    assert placed_names(CommandResult(0, output)) == ['territories.json', 'price.xlsx']
    assert placed_names(CommandResult(0, 'not json')) == []
    assert placed_names(CommandResult(0, '[]')) == []


def test_update_report() -> None:
    outcomes = {
        'Запаска (API)': CommandResult(0, '{"ok": true}'),
        'почта': CommandResult(1, '{"ok": false, "error": {"message": "нет <пароля>"}}'),
    }
    assert update_report(outcomes) == (
        '<b>Обновление прайсов поставщиков</b>\n✅ Запаска (API)\n❌ почта: нет &lt;пароля&gt;'
    )


def test_log_block() -> None:
    assert log_block('a < b') == '<pre>a &lt; b</pre>'
    assert log_block('  ') == ''
