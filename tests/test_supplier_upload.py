from pathlib import Path

from autosnab_bot.services.priceformation_cli import CommandResult
from autosnab_bot.services.supplier_upload import MAX_FILE_SIZE, PendingUpload, rejection, upload_report
from tests.fakes import make_document

MIM = 'Мим'


def test_pending_upload_collects_files(tmp_path: Path) -> None:
    pending = PendingUpload('4', MIM)
    pending.add(make_document('/x/Прайс.xlsx', file_id='a'))
    pending.add(make_document('Прайс.xlsx', file_id='b'))
    assert pending.collected_text() == f'Поставщик «{MIM}», файлов: 2\n• Прайс.xlsx\n• Прайс.xlsx'
    first = tmp_path / '0' / 'Прайс.xlsx'
    second = tmp_path / '1' / 'Прайс.xlsx'
    assert pending.targets(tmp_path) == [('a', first), ('b', second)]


def test_rejection() -> None:
    assert rejection(make_document('price.xlsx')) == ''
    assert rejection(make_document('price.csv')).startswith('Неверный формат файла')
    assert 'больше 20 МБ' in rejection(make_document('big.zip', file_size=MAX_FILE_SIZE + 1))


def test_upload_report() -> None:
    placed = CommandResult(0, '{"ok": true, "files": ["/p/mim/price.xlsx"]}')
    assert upload_report(MIM, placed) == f'Файлы поставщика «{MIM}» загружены:\n• price.xlsx'
    failed = CommandResult(1, '{"ok": false, "error": {"message": "не подходит"}}')
    assert upload_report(MIM, failed) == f'Не удалось загрузить файлы поставщика «{MIM}»: не подходит'
